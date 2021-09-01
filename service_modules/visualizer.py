import os
import sqlite3

import folium
import pandas as pd
import plotly_express as px


def create_directory(root_directory, city):
    images_directory = os.path.join(root_directory, f"{city}_visualizations")
    if not os.path.exists(images_directory):
        os.mkdir(images_directory)
    return images_directory


def create_histograms(connection, images_directory, city):
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


def create_heatmap(connection, images_directory, city, center_coordinates):
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

    def define_color(price_bins):
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


def visualize_data(city, center_coordinates, directory, batabase):
    images_directory = create_directory(directory, city)
    conn = sqlite3.connect(f"{directory}/{batabase}")
    create_histograms(conn, images_directory, city)
    create_heatmap(conn, images_directory, city, center_coordinates)
    conn.close()
    print(f"Visualisation completed. Checkout {images_directory}.")
    return
