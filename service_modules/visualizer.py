"""
Module to create visualizations for data.
"""

import os
import sqlite3
from typing import List

import folium
import pandas as pd
import plotly_express as px


def create_directory(root_directory: str, city: str) -> str:
    """
    Function that creates a directory for the visualizations
    in case there is no such. Returns path to that directory.
    :param root_directory: root directory of the project
    :type root_directory: str
    :param city: name of a city visualizations are made for
    :type city: str
    :return: path to a directory for visualizations
    :rtype: str
    """
    images_directory = os.path.join(root_directory, f"{city}_visualizations")
    if not os.path.exists(images_directory):
        os.mkdir(images_directory)
    return images_directory


def create_histograms(
    connection: "sqlite3.Connection", images_directory: str, city: str
) -> None:
    """
    Function that plots histograms "Average price by district"
    and "Average area by district" for a particular city,
    using data from a database table for that city,
    and saves them as .png files. Creates a dataframe for a chosen city,
    groups prices/areas by districts and calculates mean, plots histograms.
    :param connection: connection to the database
    :type connection: sqlite3.Connection
    :param images_directory: path to directory for created histograms
    :type images_directory: str
    :param city: name of the city, which is also a database table name
    :type city: str
    :return: None
    """
    df = pd.read_sql_query(f"SELECT * from {city}", connection)
    by_price = df.groupby(["district"])["price"].mean().reset_index(name="mean_price")
    price_histogram = px.histogram(
        data_frame=by_price,
        title="Average price by district",
        x="district",
        y="mean_price",
    )
    price_histogram.write_image(f"{images_directory}/{city}_price_per_district.png")

    by_area = df.groupby(["district"])["area"].mean().reset_index(name="mean_area")
    area_histogram = px.histogram(
        data_frame=by_area,
        title="Average area by district",
        x="district",
        y="mean_area",
    )
    area_histogram.write_image(f"{images_directory}/{city}_area_per_district.png")


def create_heatmap(
    connection: "sqlite3.Connection",
    images_directory: str,
    city: str,
    center_coordinates: List[float],
) -> None:
    """
    Function that creates an html file with visualisation of
    real estate prices per meter on a city map. Different colors
    for different price intervals are displayed.
    1) creates a dataframe for a chosen city.
    2) groups prices by location if there are multiple records for 1 location.
    3) divides total prices range for 5 equal intervals
    and adds their numbers to dataframe rows.
    4) creates a map object with city center coordinates as center.
    5) adds circles of color corresponding to price interval on the map.
    :param connection: connection to the database
    :type connection: sqlite3.Connection
    :param images_directory: path to directory for created histograms
    :type images_directory: str
    :param city: name of the city, which is also a database table name
    :type city: str
    :param center_coordinates: geographic coordinates of the city center
    :type center_coordinates: list of float
    :return: None
    """
    df = pd.read_sql_query(
        f"SELECT longitude, latitude, price_per_meter from {city}", connection
    )
    price_df = (
        df.groupby(["longitude", "latitude"])["price_per_meter"]
        .mean()
        .reset_index(name="price_per_meter")
    )
    price_df["price_bins"] = pd.qcut(
        price_df["price_per_meter"], q=5, labels=(0, 1, 2, 3, 4)
    )
    city_map = folium.Map(center_coordinates, zoom_start=11)

    def define_color(price_bins: str) -> str:
        """
        Function that returns a color name according to price interval index.
        :param price_bins: data from "price_bins" table column
        :type price_bins: str
        :return: None
        """
        colors = ["blue", "green", "yellow", "orange", "brown"]
        return colors[int(price_bins)]

    for index, row in price_df.iterrows():
        folium.CircleMarker(
            (row["latitude"], row["longitude"]),
            radius=7,
            popup=row["price_per_meter"],
            color=None,
            fill_color=define_color(row["price_bins"]),
            fill_opacity=0.2,
        ).add_to(city_map)
    city_map.save(f"{images_directory}/{city}_prices_map.html")


def visualize_data(
    city: str, center_coordinates: List[float], directory: str, database: str
) -> None:
    """
    Function that creates a directory for visualizations for a
    particular city if there's no such, creates and saves visualizations
    and informs a user when work is done.
    :param city: name of a city visualizations are made for
    :type city: str
    :param center_coordinates: geographic coordinates of the city center
    :type center_coordinates: list of float
    :param directory: root directory of the project
    :type directory: str
    :param database: name of database
    :type database: str
    :return: None
    """
    images_directory = create_directory(directory, city)
    conn = sqlite3.connect(f"{directory}/{database}")
    create_histograms(conn, images_directory, city)
    create_heatmap(conn, images_directory, city, center_coordinates)
    conn.close()
    print(f"Visualization completed. Checkout {images_directory}.")
