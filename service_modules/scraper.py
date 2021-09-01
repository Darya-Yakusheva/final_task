import asyncio
import json
import re
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from itertools import chain
from typing import Any, Iterator, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from service_modules.db_connection import (
    DataBaseConnection,
    create_db_table,
    insert_rows,
)


async def fetch_response(url: str, **kwargs: Optional[Any]) -> Optional[str]:
    """
    Function that returns web-page content asynchronously.
    :param url: url of a web-page
    :type url: str
    :param kwargs: url parameters
    :type kwargs: str
    :return: string with page content
    :rtype:str
    """

    async with aiohttp.ClientSession() as session:

        try:
            async with session.get(url, params=kwargs) as response:
                try:
                    if response.status == 200:
                        result = await response.text()
                    elif response.status in (502, 503, 504):
                        await asyncio.sleep(0.1)
                        result = await fetch_response(url, **kwargs)
                    else:
                        return
                    return result
                except aiohttp.ClientPayloadError:
                    return
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            await asyncio.sleep(0.1)
            await fetch_response(url, **kwargs)


async def get_multiple_pages_content(*urls: str, pages: range = None) -> Iterator:
    """
    Function that returns list of contents of given web-pages asynchronously.
    Takes either a collection of urls, or a single url and a range of pages.
    :param urls: url or collection of urls of web-pages
    :type urls: str or collection of str
    :param pages: range of pages to be passed as parameters to URL address.
    :return: optional range
    :rtype: list of str
    """
    if pages:
        tasks = [
            asyncio.create_task(fetch_response(*urls, Page=page)) for page in pages
        ]
    else:
        tasks = [asyncio.create_task(fetch_response(url)) for url in urls]
    await asyncio.gather(*tasks)
    result = (task.result() for task in tasks)
    return filter(lambda x: x, result)


def get_number_of_last_page(url: str) -> int:
    """
    Function that finds number of the last page with search results.
    :param url: URL address of search page of a particular city
    :type url: str
    :return: number of last page with search results
    :rtype: int
    """
    page_content = asyncio.run(fetch_response(url))
    main_page = BeautifulSoup(page_content, "html.parser")
    pagination_section = main_page.find(
        "div", class_="pagination__pagesContainer___up6kR"
    )
    last_page = pagination_section.find_all("a")[-1].text
    return int(last_page)


def get_apartment_urls_from_single_page(domain: str, search_page: str) -> List[str]:
    """Function that returns all URL-addresses of apartment offers
    from a single web-page"""
    soup = BeautifulSoup(search_page, "html.parser")
    table = soup.find("div", class_="search-results__itemCardList___RdWje").find_all(
        "a"
    )
    flats_urls = [domain + row.get("href") for row in table]
    return flats_urls


def get_apartment_urls_from_multiple_pages(domain: str, all_search_pages) -> Iterator:
    """
    Function that runs get_apartment_urls_from_single_page function
    on all search pages using multiprocessing.
    """
    with ProcessPoolExecutor() as executor:
        result = executor.map(
            partial(get_apartment_urls_from_single_page, domain), all_search_pages
        )
    return chain(*result)


def get_single_apartment_data(city, html):
    """
    Function that collects all necessary information from a single
    apartment offers
    """
    try:
        district = "district" if city == "ekaterinburg" else "adminDistrict"
        soup = BeautifulSoup(html, "html.parser")
        res = soup.find("script", text=re.compile("window.__INITIAL_DATA__*")).string[
            26:
        ]
        info = json.loads(res)["itemState"]["item"]
        admin_district = info[district]["name"].split()[0]
        location_longitude = info["location"]["longitude"]
        location_latitude = info["location"]["latitude"]
        area = info["floorAreaCalculated"]
        price = info["priceValue"]
        price_meter = info["pricePerAreaValue"]
    except (KeyError, TypeError):
        return None
    else:
        return (
            admin_district,
            location_longitude,
            location_latitude,
            area,
            price,
            price_meter,
        )


def get_multiple_apartment_data(city, all_apartment_urls):
    """
    Function that runs get_single_apartment_data function
    on all search pages using multiprocessing.
    """
    with ProcessPoolExecutor() as executor:
        result = executor.map(
            partial(get_single_apartment_data, city), all_apartment_urls
        )
    return filter(lambda x: x, result)


def get_all_necessary_data(city, domain, search_url, pages):
    all_search_pages = asyncio.run(get_multiple_pages_content(search_url, pages=pages))
    all_apt_urls = get_apartment_urls_from_multiple_pages(domain, all_search_pages)
    all_apt_htmls = asyncio.run(get_multiple_pages_content(*all_apt_urls))
    all_apt_data = get_multiple_apartment_data(city, all_apt_htmls)
    return all_apt_data


def scrape_and_save(DIRECTORY, DB_NAME, city, domain, search_url):

    last_page = get_number_of_last_page(search_url)
    print(f"""{last_page} pages of real estate offers found.\nScraping started...""")
    all_search_pages = range(1, last_page + 1)
    n_pages_by_iteration = 40
    progress = 0
    percent = n_pages_by_iteration / last_page * 100

    with DataBaseConnection(f"{DIRECTORY}/{DB_NAME}") as connection:
        conn = connection.connection
        cur = connection.cursor
        cur.execute(f"DROP TABLE {city};")
        conn.commit()
        cur.execute(create_db_table(city))

        while all_search_pages:
            next_pages = all_search_pages[:n_pages_by_iteration]
            data = get_all_necessary_data(city, domain, search_url, next_pages)
            for data_row in data:
                cur.execute(insert_rows(city, data_row))
            conn.commit()
            progress += percent
            print(
                f"--- {round(progress, 2)}% of real estate data has been collected ---"
            )
            all_search_pages = all_search_pages[n_pages_by_iteration:]
        print("Real estate data completed.")
    return
