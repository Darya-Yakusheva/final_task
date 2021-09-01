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


def create_db_table(table):
    """Function to create new table for a city"""
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


def insert_rows(table, data_row):
    """Function to save data to a table of a city"""
    columns = "'district', 'longitude', 'latitude', 'area', 'price', 'price_per_meter'"
    return f"INSERT INTO {table} ({columns}) VALUES {data_row};"
