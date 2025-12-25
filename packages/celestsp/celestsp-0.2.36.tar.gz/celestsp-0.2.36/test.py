#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

import networkx as nx
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

# Insert the src directory (which contains the macocr package) into sys.path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import the module under test
from celestsp.main import CelestialTSP, main


# This dummy object will emulate the result of SkyCoord.transform_to.
class DummyAltAz:
    def __init__(self, alt):
        # alt is assumed to be a scalar (float) altitude in degrees.
        self.alt = type("dummy_alt", (), {"deg": alt})
        self.az = type("dummy_az", (), {"deg": 100.0})


# A dummy version of SkyCoord.transform_to.
def dummy_transform_to(self, frame):
    """
    This dummy inspects self.ra.deg: if it is less than 1 then returns an altitude of 10,
    otherwise returns an altitude of 5.
    For vectorized calls (when frame.obstime is an array) the altitude will linearly decrease
    from the chosen value to below 0 so that the first time a set condition is met can be computed.
    """
    dummy_alt = 10.0 if self.ra.deg < 1.0 else 5.0
    # If the frame has an "obstime" attribute, check if it is array-like.
    if hasattr(frame, "obstime"):
        try:
            # if frame.obstime is iterable (vectorized call)
            n = len(frame.obstime)
        except TypeError:
            n = None
        if n is not None:
            # Create a linearly decreasing altitude array:
            # altitude will drop from dummy_alt at t=0 to -1 at t=end.
            alts = dummy_alt - (dummy_alt + 1) * np.linspace(0, 1, n)
            dummy_alt_obj = type("DummyAltArray", (), {})()
            dummy_alt_obj.deg = alts
            dummy_az_obj = type("DummyAzArray", (), {})()
            dummy_az_obj.deg = np.full(n, 100.0)
            dummy = type("Dummy", (), {})()
            dummy.alt = dummy_alt_obj
            dummy.az = dummy_az_obj
            return dummy
        else:
            # Scalar call: return a constant dummy object.
            return DummyAltAz(dummy_alt)
    else:
        return DummyAltAz(dummy_alt)


# A dummy version of SkyCoord.from_name for testing read_celestial_names.
def dummy_from_name(name):
    # Return a dummy SkyCoord with RA and Dec based on the name string.
    # For example, if name can be converted to a float then use that value;
    # otherwise use fixed numbers.
    try:
        ra_val = float(name)
    except ValueError:
        ra_val = 15.0
    # Use dec = ra/2 for testing.
    dec_val = ra_val / 2.0
    dummy = SkyCoord(ra=ra_val * u.deg, dec=dec_val * u.deg)
    return dummy


# A dummy requests.get to simulate get_location.
def dummy_requests_get_success(url):
    # Simulate a successful response.
    response = MagicMock()
    response.json.return_value = {"status": "success", "lat": 35.0, "lon": -120.0}
    return response


def dummy_requests_get_fail(url):
    # Simulate a failed location response.
    response = MagicMock()
    response.json.return_value = {"status": "fail"}
    return response


# --- The test class --- #
class TestCelestialTSP(unittest.TestCase):
    def setUp(self):
        # Create dummy arguments similar to build_arg_parser but overriding defaults.
        self.temp_input = tempfile.NamedTemporaryFile(
            delete=False, mode="w", encoding="utf-8"
        )
        # Write some dummy celestial names (each name on its own line).
        # We choose names that when passed to dummy_from_name produce specific RA/Dec values.
        self.temp_input.write(
            "0\n1\nNonNumeric"
        )  # first two numeric, third will use default 15.0.
        self.temp_input.close()
        # Build a dummy argparse.Namespace
        self.args = argparse.Namespace(
            input_file_path=self.temp_input.name,
            lat=0.0,
            lon=0.0,
            height=0.0,
            date="2023-01-01",
            time="00:00:00",
            tz="+0",
            output="test_output",
            first_body="",
            default_datetime=False,
        )
        # Create a CelestialTSP instance with dummy args.
        self.planner = CelestialTSP(self.args)

    def tearDown(self):
        if os.path.exists(self.temp_input.name):
            os.unlink(self.temp_input.name)
        # Remove any files created by save_spherical_image if necessary.
        for f in os.listdir("."):
            if f.startswith(self.args.output) and f.endswith(".png"):
                os.unlink(f)

    @patch("celestsp.main.SkyCoord.from_name", side_effect=dummy_from_name)
    def test_read_celestial_names_success(self, mock_from_name):
        # Test that read_celestial_names returns a DataFrame with valid data.
        df = self.planner.read_celestial_names(self.args.input_file_path)
        self.assertFalse(df.empty)
        self.assertIn("Name", df.columns)
        self.assertIn("RA", df.columns)
        self.assertIn("Dec", df.columns)
        # Three lines in our file.
        self.assertEqual(len(df), 3)

    def test_read_celestial_names_file_not_exist(self):
        # Provide a non-existent file path.
        fake_path = "nonexistent_file.txt"
        with (
            self.assertRaises(SystemExit) as cm,
            patch("sys.stdout", new=io.StringIO()) as fake_out,
        ):
            self.planner.read_celestial_names(fake_path)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("does not exist", fake_out.getvalue())

    @patch("celestsp.main.SkyCoord.from_name", side_effect=dummy_from_name)
    def test_read_celestial_names_empty(self, mock_from_name):
        # Create an empty temporary file.
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            empty_path = tmp.name
        try:
            with (
                self.assertRaises(SystemExit) as cm,
                patch("sys.stdout", new=io.StringIO()) as fake_out,
            ):
                self.planner.read_celestial_names(empty_path)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn(
                "empty or contains no valid celestial names", fake_out.getvalue()
            )
        finally:
            os.unlink(empty_path)

    def test_is_observable(self):
        # Create a dummy altaz object with alt.deg = 5.
        dummy = DummyAltAz(5)
        self.assertTrue(CelestialTSP.is_observable(dummy))
        # Test below horizon.
        dummy2 = DummyAltAz(-1)
        self.assertFalse(CelestialTSP.is_observable(dummy2))
        # Test with min_altitude argument.
        self.assertFalse(CelestialTSP.is_observable(dummy, min_altitude=6))

    def test_make_graph(self):
        # Prepare simple coordinates and distance matrix.
        coords = np.array([[10, 20], [30, 40], [50, 60]])
        dist_mat = np.array([[0, 1, 2], [1, 0, 3], [2, 3, 0]])
        graph = CelestialTSP.make_graph(coords, dist_mat)
        self.assertIsInstance(graph, nx.Graph)
        # Check nodes and edge weights.
        self.assertEqual(len(graph.nodes), 3)
        self.assertEqual(len(graph.edges), 3)  # complete graph of 3 nodes: 3 edges.
        self.assertAlmostEqual(graph[0][1]["weight"], 1)

    def test_show_results(self):
        # Create a dummy DataFrame with required columns.
        df = pd.DataFrame(
            {
                "Name": ["A", "B"],
                "RA": [10.0, 20.0],
                "Dec": [5.0, 15.0],
                "Altitude": [30.0, 20.0],
                "Azimuth": [40.0, 50.0],
                "TimeToSet": [2.0, 3.0],
                "Observable": [True, False],
            }
        )
        # Capture printed output.
        out = io.StringIO()
        with redirect_stdout(out):
            CelestialTSP.show_results(df)
        result = out.getvalue()
        self.assertIn("Optimal Order of Celestial Bodies", result)
        self.assertIn("A", result)
        self.assertIn("B", result)

    def test_save_spherical_image(self):
        # Create a dummy DataFrame with required columns.
        df = pd.DataFrame(
            {
                "Name": ["A", "B", "C"],
                "RA": [10.0, 20.0, 30.0],
                "Dec": [5.0, 15.0, 25.0],
                "Altitude": [80.0, 70.0, 60.0],
                "Azimuth": [40.0, 50.0, 60.0],
                "TimeToSet": [2.0, 3.0, 4.0],
                "Observable": [True, True, False],
            }
        )
        location_str = "Test Location"
        observation_time = Time("2023-01-01 00:00:00")
        # Patch plt.savefig so no file is written.
        with (
            patch("celestsp.main.plt.savefig") as mock_savefig,
            patch("datetime.datetime") as mock_datetime,
        ):
            mock_datetime.now.return_value = datetime.datetime(2023, 1, 1, 0, 0, 0)
            CelestialTSP.save_spherical_image(
                df, location_str, observation_time, "dummy_output"
            )
            # Assert that savefig was called.
            mock_savefig.assert_called()

    def test_get_location_success(self):
        with patch(
            "celestsp.main.requests.get", side_effect=dummy_requests_get_success
        ):
            lat, lon = CelestialTSP.get_location()
            self.assertEqual(lat, 35.0)
            self.assertEqual(lon, -120.0)

    def test_get_location_fail(self):
        with patch("celestsp.main.requests.get", side_effect=dummy_requests_get_fail):
            lat, lon = CelestialTSP.get_location()
            self.assertIsNone(lat)
            self.assertIsNone(lon)

    def test_build_arg_parser(self):
        # To make sure build_arg_parser returns the expected Namespace,
        # we simulate a command-line call by patching sys.argv.
        args_list = [
            self.temp_input.name,
            "--lat",
            "12.34",
            "--lon",
            "56.78",
            "--height",
            "100",
            "--date",
            "2023-12-31",
            "--time",
            "23:59:59",
            "--tz",
            "+3",
            "--output",
            "my_results.png",
            "--first_body",
            "TestBody",
        ]
        with patch.object(sys, "argv", ["prog"] + args_list):
            with patch(
                "celestsp.main.CelestialTSP.get_location", return_value=(1.0, 2.0)
            ):
                parser_args = CelestialTSP.build_arg_parser()
                self.assertEqual(parser_args.input_file_path, self.temp_input.name)
                self.assertEqual(parser_args.lat, 12.34)
                self.assertEqual(parser_args.lon, 56.78)
                self.assertEqual(parser_args.height, 100)
                self.assertEqual(parser_args.date, "2023-12-31")
                self.assertEqual(parser_args.time, "23:59:59")
                self.assertEqual(parser_args.tz, "+3")
                self.assertEqual(parser_args.output, "my_results.png")
                self.assertEqual(parser_args.first_body, "TestBody")

    @patch("celestsp.main.SkyCoord.from_name", side_effect=dummy_from_name)
    @patch("celestsp.main.SkyCoord.transform_to", new=dummy_transform_to)
    @patch("celestsp.main.nx.approximation.greedy_tsp", return_value=[1, 0, 2])
    def test_run_with_first_body_not_specified(self, mock_tsp, mock_from_name):
        # Test the full run() method when first_body is not provided.
        # First, read celestial names.
        self.planner.df = self.planner.read_celestial_names(self.args.input_file_path)
        # We expect find_first_body to use our dummy transform_to.
        # With our dummy, rows with RA < 1 get altitude 10 and others get altitude 5.
        # In our test file, the first entry is "0", so RA = 0 and altitude=10; the second is "1"
        # (RA = 1 gives altitude=5) and third is "NonNumeric" -> RA =15 so altitude=5.
        # When computing t_set in find_first_body the one with lower dummy altitude (5) will set earlier.
        out = io.StringIO()
        with redirect_stdout(out):
            # Because run() eventually calls sys.exit(1) if first_body provided is invalid.
            # In this run we'll not provide first_body so find_first_body returns an index.
            self.planner.run()
        # In our dummy simulation, first_index should be 1 (the second row).
        printed = out.getvalue()
        self.assertIn("Location:", printed)
        self.assertIn("Observation Date/Time:", printed)
        # Because all plotting and file saving functions are exercised, check that the output contains the plot saved message.
        self.assertIn("Plot saved as", printed)

    @patch("celestsp.main.SkyCoord.from_name", side_effect=dummy_from_name)
    def test_run_with_invalid_first_body(self, mock_from_name):
        # Set a first_body that is not in the file.
        self.args.first_body = "NonExistent"
        self.planner = CelestialTSP(self.args)
        # read the file (will read three lines and get dataframe)
        self.planner.df = self.planner.read_celestial_names(self.args.input_file_path)
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            self.planner.run()
        printed = out.getvalue()
        self.assertIn("is not in the input file.", printed)


# Test the module level main() function.
class TestMainFunction(unittest.TestCase):
    @patch("celestsp.main.CelestialTSP.build_arg_parser")
    @patch("celestsp.main.CelestialTSP.run")
    def test_main(self, mock_run, mock_build_arg_parser):
        # Create a dummy Namespace to be returned by build_arg_parser.
        dummy_args = argparse.Namespace(
            input_file_path="dummy.txt",
            lat=0.0,
            lon=0.0,
            height=0.0,
            date="2023-01-01",
            time="00:00:00",
            tz="+0",
            output="dummy_output",
            first_body="",
            default_datetime=True,
        )
        mock_build_arg_parser.return_value = dummy_args
        # Run main() and make sure run() is called.
        with patch("sys.stdout", new=io.StringIO()):
            main()
            mock_run.assert_called()


if __name__ == "__main__":
    unittest.main()
