"""
Module to create a context manager for a database
and and define functions for database table creation and data insertion
"""

import sqlite3
from datetime import date


class DataBaseConnection:
    """
    Class for connecting to database and committing changes
    to be used as a context manager.
    """

    def __init__(self, database_name: str) -> None:
        """
        Class initializer method.
        :param database_name: name of database
        :type database_name: str
        """
        self.connection = sqlite3.connect(database_name)
        self.cursor = self.connection.cursor()

    def __enter__(self) -> "DataBaseConnection":
        """
        Method defining what context manager should do at the beginning.
        :return: class instance itself (bound to target)
        :rtype: class: "DataBaseConnection"
        """
        return self

    def __exit__(self, *args: str) -> None:
        """
        Method defining what context manager should do at the end.
        :param args: exception type, exception value, traceback
        :return: None
        """
        self.connection.commit()
        self.cursor.close()
        self.connection.close()


def create_db_table(table: str):
    """
    Function to create new table for a city.
    :param table: name of the city to create a table for it
    :type table: str
    """
    table_structure = f"""
    id integer PRIMARY KEY NULL,
    district VARCHAR NOT NULL,
    longitude REAL NOT NULL,
    latitude REAL NOT NULL,
    area REAL NOT NULL,
    price REAL NOT NULL,
    price_per_meter REAL NOT NULL,
    creation_date TEXT DEFAULT "{str(date.today())}"
    """
    return f"CREATE TABLE IF NOT EXISTS {table} ({table_structure});"


def insert_rows(table: str, data_row: tuple):
    """
    Function to insert a data row to a table of a city.
    :param table: name of the table to insert data
    :type table: str
    :param data_row: data to insert into table row
    :type data_row: tuple
    """
    columns = "'district', 'longitude', 'latitude', 'area', 'price', 'price_per_meter'"
    return f"INSERT INTO {table} ({columns}) VALUES {data_row};"
