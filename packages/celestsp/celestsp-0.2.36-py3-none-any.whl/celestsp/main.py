#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.projections.polar import PolarAxes
import networkx as nx
from scipy.spatial import distance_matrix
from astropy.coordinates import SkyCoord, EarthLocation, AltAz  # type: ignore
from astropy.time import Time  # type: ignore
from astropy import units as u  # type: ignore
from typing import cast
import datetime


class CelestialTSP:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.location = EarthLocation(lat=args.lat, lon=args.lon, height=args.height)
        self.location_str = f"Lat: {args.lat}, Lon: {args.lon}, Height: {args.height}m"
        # If a “default date/time” was provided then no timezone conversion is required.
        if args.default_datetime:
            self.observation_time = Time(f"{args.date} {args.time}")
        else:
            self.observation_time = (
                Time(f"{args.date} {args.time}") - int(args.tz) * u.hour
            )
        self.df: pd.DataFrame = pd.DataFrame()

    def run(self):
        # 1. Read celestial names/coordinates from file.
        self.df = self.read_celestial_names(self.args.input_file_path)

        # 2. Check if first_body name is provided and valid.
        if self.args.first_body:
            # Instead of int(self.df.index[...][0]), we explicitly get the index.
            matching_indices = self.df.index[self.df["Name"] == self.args.first_body]
            if matching_indices.empty:
                print(f"Error: {self.args.first_body} is not in the input file.")
                sys.exit(1)
            first_index = int(matching_indices[0])  # type: ignore
        else:
            first_index = self.find_first_body()

        print(f"Location: {self.location_str}")
        print(
            f"Observation Date/Time: {self.args.date} {self.args.time} {self.args.tz}"
        )

        # 3. Build a graph for all celestial bodies:
        # We use their (Altitude, Azimuth) values.
        coordinates = self.df[["Altitude", "Azimuth"]].to_numpy()
        dmatrix = distance_matrix(coordinates, coordinates)
        if first_index != -1:
            graph = self.make_graph(coordinates, dmatrix)
            tsp_path = nx.approximation.greedy_tsp(graph, source=first_index)
            df_ordered = self.df.iloc[tsp_path].reset_index(drop=True)
            self.show_results(df_ordered)
            self.save_spherical_image(
                df_ordered, self.location_str, self.observation_time, self.args.output
            )
        else:
            print(
                "Could not find the celestial body closest to the west (270° azimuth)."
            )

    def read_celestial_names(self, file_path: str) -> pd.DataFrame:
        """
        Reads a file with celestial object names and retrieves their RA/Dec using astropy.
        Exits with error if file cannot be found or no valid data is returned.
        """
        if not os.path.exists(file_path):
            print(f"Input file {file_path} does not exist.")
            sys.exit(1)

        records = []
        with open(file_path, "r") as f:
            for line in f:
                name = line.strip()
                try:
                    coord = SkyCoord.from_name(name)
                    records.append(
                        {"Name": name, "RA": coord.ra.deg, "Dec": coord.dec.deg}
                    )
                except Exception as e:
                    print(f"Error looking up {name}: {e}")
                    continue
        df = pd.DataFrame(records)
        if df.empty:
            print("Input file is empty or contains no valid celestial names.")
            sys.exit(1)
        return df

    def find_first_body(self) -> int:
        """
        Identify the celestial body that will set first (i.e. has the shortest time until setting)
        when observed from self.location at self.observation_time.
        The method also adds several columns to self.df: Altitude, Azimuth, TimeToSet, Observable.
        Returns the row index of this first body.
        """
        altaz_frame = AltAz(obstime=self.observation_time, location=self.location)

        # Pre-create lists (can be replaced with vectorized operations if desired)
        altitudes = []
        azimuths = []
        times_to_set = []
        observables = []
        shortest_time = np.inf
        first_index = -1

        # For each row we can optimize by processing in bulk. However, because the time-to-set
        # calculation uses a simulated time grid, we loop for clarity.
        for i, row in self.df.iterrows():
            sky_coord = SkyCoord(ra=row["RA"], dec=row["Dec"], unit="deg")
            altaz = sky_coord.transform_to(altaz_frame)
            alt = altaz.alt.deg
            az = altaz.az.deg
            altitudes.append(alt)
            azimuths.append(az)
            observables.append(self.is_observable(altaz))

            # If object is currently above horizon compute when it will set
            if alt > 0:
                # Create a time grid (1000 steps within 24h)
                delta_hours = np.linspace(0, 24, 1000) * u.hour
                future_times = self.observation_time + delta_hours
                future_altaz = sky_coord.transform_to(
                    AltAz(obstime=future_times, location=self.location)
                )
                future_alts = future_altaz.alt.deg
                # Find first time when altitude goes non-positive (object sets)
                set_indices = np.where(future_alts <= 0)[0]
                if set_indices.size > 0:
                    t_set = (
                        (future_times[set_indices[0]] - self.observation_time)
                        .to(u.hour)
                        .value
                    )
                    times_to_set.append(t_set)
                    if t_set < shortest_time:
                        shortest_time = t_set
                        first_index = i  # type: ignore
                else:
                    times_to_set.append(np.inf)
            else:
                times_to_set.append(np.inf)

        self.df["Altitude"] = altitudes
        self.df["Azimuth"] = azimuths
        self.df["TimeToSet"] = times_to_set
        self.df["Observable"] = observables

        return first_index

    @staticmethod
    def is_observable(altaz_coord, min_altitude=0) -> bool:
        """Return True if the altitude is above min_altitude (default=0 deg)."""
        return altaz_coord.alt.deg > min_altitude

    @staticmethod
    def make_graph(coordinates: np.ndarray, dist_matrix: np.ndarray) -> nx.Graph:
        """
        Builds a fully-connected NetworkX graph where each node represents a celestial object.
        Node positions (for plotting) are stored in the 'pos' attribute; edge weights are from distance matrix.
        """
        G: nx.Graph = nx.Graph()
        n = len(coordinates)
        for i in range(n):
            G.add_node(i, pos=(coordinates[i][0], coordinates[i][1]))
        # Use upper-triangle of matrix (graph undirected)
        for i in range(n):
            for j in range(i + 1, n):
                G.add_edge(i, j, weight=dist_matrix[i, j])
        return G

    @staticmethod
    def show_results(df: pd.DataFrame) -> None:
        """Prints the optimal order of celestial bodies."""
        print("\nOptimal Order of Celestial Bodies:")
        for i, row in df.iterrows():
            if int(i) + 1 == len(df):  # type: ignore
                continue
            name = row["Name"]
            ra = f"{row['RA']:.2f}"
            dec = f"{row['Dec']:.2f}"
            alt = f"{row['Altitude']:.2f}"
            azimuth = f"{row['Azimuth']:.2f}"
            tset = f"{row['TimeToSet']:.2f}"
            observable = row["Observable"]
            print(
                f"Name: {name:<10} RA: {ra:<7} Dec: {dec:<7} Altitude: {alt:<7} Azimuth: {azimuth:<7} Time to set: {tset:<7} Observable: {observable}"
            )

    @staticmethod
    def save_spherical_image(
        df: pd.DataFrame, location_str: str, observation_time: Time, filename: str
    ) -> None:
        """
        Generate and save a spherical (polar) plot showing celestial object positions
        and the TSP path.
        """
        fig = plt.figure(figsize=(8, 8))
        ax = cast(PolarAxes, fig.add_subplot(111, projection="polar"))

        az_radians = np.deg2rad(df["Azimuth"])
        alt_radians = np.deg2rad(90 - df["Altitude"])

        ax.scatter(az_radians, alt_radians, c="blue", label="Celestial Bodies")
        for i, row in df.iterrows():
            ax.annotate(
                row["Name"], (az_radians[i], alt_radians[i]), fontsize=8, ha="right"
            )

        for i in range(len(df) - 1):
            start_az, start_alt = az_radians[i], alt_radians[i]
            end_az, end_alt = az_radians[i + 1], alt_radians[i + 1]
            ax.plot([start_az, end_az], [start_alt, end_alt], "r-")

        if len(df) > 0:
            start_az, start_alt = az_radians.iloc[0], alt_radians.iloc[0]
            ax.annotate(
                "Start",
                xy=(start_az, start_alt),
                xytext=(start_az, start_alt + 0.1),
                fontsize=12,
                color="green",
                ha="center",
            )
            if len(df) > 1:
                second_az, second_alt = az_radians.iloc[1], alt_radians.iloc[1]
                ax.annotate(
                    "",
                    xy=(second_az, second_alt),
                    xytext=(start_az, start_alt),
                    arrowprops=dict(facecolor="red", arrowstyle="->", lw=2.5),
                )

        ax.set_title("Optimal Order of Celestial Bodies (Spherical Projection)", pad=30)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)

        obs_time_str = (
            observation_time.iso if observation_time is not None else "Unknown"
        )
        fig.text(
            0.5,
            0.01,
            f"Location: {location_str} | Observation Time: {obs_time_str} UTC",
            ha="center",
            fontsize=10,
        )
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            plt.savefig(f"{filename}_{now}.png")
            print(f"Plot saved as {filename}_{now}.png")
        except Exception as e:
            print(f"Error saving plot: {e}")
        plt.close()

    @staticmethod
    def get_location() -> tuple:
        """
        Obtain the current location by using ip-api.com.
        Returns a tuple (latitude, longitude) or (None, None) if unavailable.
        """
        try:
            response = requests.get("http://ip-api.com/json/")
            data = response.json()
            if data.get("status") == "success":
                return float(data.get("lat")), float(data.get("lon"))
            else:
                print("Error: Unable to get location data")
                return None, None
        except Exception:
            return None, None

    @classmethod
    def build_arg_parser(cls) -> argparse.Namespace:
        """
        Set up and parse command-line arguments.
        """
        latitude, longitude = cls.get_location()
        # Get current time string for default values.
        now = Time.now().iso.split(".")[0]
        date_default, time_default = now.split(" ")
        parser = argparse.ArgumentParser(description="Celestial TSP Planner")
        parser.add_argument(
            "input_file_path",
            type=str,
            help="Input file path with celestial coordinates.",
        )
        parser.add_argument(
            "--lat",
            type=float,
            default=latitude if latitude is not None else 0,
            help="Latitude of observation location.",
        )
        parser.add_argument(
            "--lon",
            type=float,
            default=longitude if longitude is not None else 0,
            help="Longitude of observation location.",
        )
        parser.add_argument(
            "--height",
            type=float,
            default=0,
            help="Height of observation location (in meters).",
        )
        parser.add_argument(
            "--date",
            type=str,
            default=date_default,
            help="Observation date (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--time",
            type=str,
            default=time_default,
            help="Observation time (HH:MM:SS).",
        )
        parser.add_argument(
            "--tz", type=str, default="+9", help="Time zone offset (e.g., +9 for JST)."
        )
        parser.add_argument(
            "--output",
            type=str,
            default="results",
            help="Filename for the output image.",
        )
        parser.add_argument(
            "--first_body",
            type=str,
            default="",
            help="Name of the celestial body to start the TSP from.",
        )
        args, _ = parser.parse_known_args()
        args.default_datetime = args.date == date_default and args.time == time_default
        return args


def main():
    # Parse command line arguments
    args = CelestialTSP.build_arg_parser()
    # Create and run the CelestialTSP planner
    planner = CelestialTSP(args)
    planner.run()


if __name__ == "__main__":
    main()
