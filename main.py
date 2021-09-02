"""
Module to interact with a user and run functions for chosen operations.
"""

import os

from service_modules.db_connection import DataBaseConnection
from service_modules.scraper import scrape_and_save
from service_modules.setup_data import Cities
from service_modules.visualizer import visualize_data

DB_NAME = "real_estate.db"
DIRECTORY = os.path.abspath(os.path.dirname(__file__))


def get_data_date(city: str) -> str:
    """
    Function to return date of a database table creation.
    :param city: name of the city, which is also a database table name
    :type city: str
    :return: date of a database table creation
    :rtype str
    """
    with DataBaseConnection(DB_NAME) as conn:
        date = conn.cursor.execute(f"""SELECT creation_date FROM {city}""").fetchone()
        return date[0]


def choose_mode(choice: str) -> None:
    """
    Function to interact with a user and perform a chosen operation.
    :param choice: city abbreviation of a chosen city
    :type choice: str
    :return: None
    """
    city = Cities(choice)
    date = get_data_date(city.name)
    mode = input(
        f"""
\nData in database was collected on {date}.
Please input letter for program to perform:
'v' - for visualization of existing data
'c' - for collecting actual data (WARNING: this operation can not be undone
and will take several hours to be completed)
Or input 'b' to return to main menu.
"""
    )
    if mode not in "bcv":
        print("Invalid input")
    if mode == "v":
        visualize_data(city.name, city.center_coordinates, DIRECTORY, DB_NAME)
    if mode == "c":
        scrape_and_save(DIRECTORY, DB_NAME, city.name, city.homepage, city.search_url)
    return


def main():
    """Main function to interact with a user when script is run"""
    while True:
        choice = input(
            """
\nInput abbreviation for city to get data:
'ekb' - Ekaterinburg
'msk' - Moscow
'spb' - Saint-Petersburg
or 'q' to exit.
"""
        )
        if choice == "q":
            exit()
        elif choice in ["ekb", "msk", "spb"]:
            choose_mode(choice)
        else:
            print("Invalid input.")


if __name__ == "__main__":
    main()
