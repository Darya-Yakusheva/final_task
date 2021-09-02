"""
Module to scrape data from a website and save it to a database.
"""

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


async def get_multiple_pages_content(*urls: str, pages: range = None) -> Iterator[str]:
    """
    Function that returns list of contents of given web-pages asynchronously.
    Takes either a collection of urls, or a single url and a range of pages.
    :param urls: url or collection of urls of web-pages
    :type urls: str or collection of str
    :param pages: range of pages to be passed as parameters to URL address.
    :return: optional range
    :rtype: iterator of str
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


def get_apartment_urls_from_single_page(homepage: str, search_page: str) -> List[str]:
    """
    Function that returns all URL-addresses of apartment offers
    from a single web-page.
    :param homepage: URL-address of a homepage of a real estate website
    :type homepage: str
    :param search_page: search page content (html)
    :type search_page: str
    :return: list of URL-addresses of apartment offers on the search page
    :rtype: list of str
    """
    soup = BeautifulSoup(search_page, "html.parser")
    table = soup.find("div", class_="search-results__itemCardList___RdWje").find_all(
        "a"
    )
    flats_urls = [homepage + row.get("href") for row in table]
    return flats_urls


def get_apartment_urls_from_multiple_pages(
    homepage: str, all_search_pages: Iterator[str]
) -> Iterator[str]:
    """
    Function that runs get_apartment_urls_from_single_page function
    on all search pages using multiprocessing.
    :param homepage: URL-address of a homepage of a real estate website
    :type homepage: str
    :param all_search_pages: URL addresses of multiple search pages
    :type all_search_pages: iterator of str
    :return:
    """
    with ProcessPoolExecutor() as executor:
        result = executor.map(
            partial(get_apartment_urls_from_single_page, homepage), all_search_pages
        )
    return chain(*result)


def get_single_apartment_data(city: str, html: str) -> Optional[tuple]:
    """
    Function that collects all necessary information from a single
    apartment offers.
    :param city: name of the city where search is performed
    :type city: str
    :param html: page content of a single apartment web-page
    :type html: str
    :return: tuple of data for the apartment or None if any data is missing
    :rtype: optional tuple
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


def get_multiple_apartment_data(
    city: str, all_apartment_urls: Iterator[str]
) -> Iterator[tuple]:
    """
    Function that runs get_single_apartment_data function
    on multiple search pages using multiprocessing.
    :param city: name of the city where search is performed
    :type city: str
    :param all_apartment_urls: URL addresses of multiple apartment web pages
    :type all_apartment_urls: iterator of str
    :return: tuples of necessary data for multiple apartments
    :rtype: iterator of tuples
    """
    with ProcessPoolExecutor() as executor:
        result = executor.map(
            partial(get_single_apartment_data, city), all_apartment_urls
        )
    return filter(lambda x: x, result)


def get_all_necessary_data(
    city: str, homepage: str, search_url: str, pages: range
) -> Iterator[tuple]:
    """
    Function that gets all necessary information from web-pages of apartments
    present on a given range of search pages.
    1) gets contents of given range of search pages.
    2) gets all URL-addresses of apartment offers from those pages contents.
    3) gets contents of all apartment offers pages from those URLs.
    4) collects necessary data from those contents and returns it.
    :param city: name of the city where search is performed
    :type city: str
    :param homepage: URL-address of a homepage of a real estate website
    :type homepage str
    :param search_url: URL address of search results page for a particular city
    :type search_url: str
    :param pages: range of search pages
    :type pages: range
    :return: tuples of necessary data for multiple apartments
    :rtype: iterator of tupleas
    """
    all_search_pages = asyncio.run(get_multiple_pages_content(search_url, pages=pages))
    all_apt_urls = get_apartment_urls_from_multiple_pages(homepage, all_search_pages)
    all_apt_htmls = asyncio.run(get_multiple_pages_content(*all_apt_urls))
    all_apt_data = get_multiple_apartment_data(city, all_apt_htmls)
    return all_apt_data


def scrape_and_save(
    directory: str, db_name: str, city: str, homepage: str, search_url: str
) -> None:
    """
    Function that scrapes data in a loop by n_pages_by_iteration" pages
    to avoid excessive memory usage, and saves results to database.
    1) finds number of the last search page.
    2) sets number of search pages to process on each iteration
    (n_pages_by_iteration) and calculates its percentage from total.
    3) drops existing table from database and creates a new one.
    4) processes n search pages (gets data, writes it to db,
    shows progress to a user) until there'll be no search pages left.
    :param directory: root directory of the project where DB is located
    :type directory: str
    :param db_name: name of database
    :type db_name: str
    :param city: name of the city, which is also a database table name
    :type city: str
    :param homepage: URL-address of a homepage of a real estate website
    :type homepage: str
    :param search_url: URL-address of search results page for a chosen city
    :type search_url: str
    :return: None
    """
    last_page = get_number_of_last_page(search_url)
    print(f"""{last_page} pages of real estate offers found.\nScraping started...""")
    all_search_pages = range(1, last_page + 1)
    n_pages_by_iteration = 40
    progress = 0
    percent = n_pages_by_iteration / last_page * 100

    with DataBaseConnection(f"{directory}/{db_name}") as connection:
        conn = connection.connection
        cur = connection.cursor
        cur.execute(f"DROP TABLE {city};")
        conn.commit()
        cur.execute(create_db_table(city))

        while all_search_pages:
            next_pages = all_search_pages[:n_pages_by_iteration]
            data = get_all_necessary_data(city, homepage, search_url, next_pages)
            for data_row in data:
                cur.execute(insert_rows(city, data_row))
            conn.commit()
            progress += percent
            print(
                f"--- {round(progress, 2)}% of real estate data has been collected ---"
            )
            all_search_pages = all_search_pages[n_pages_by_iteration:]
        print("Real estate data scraping completed.")
