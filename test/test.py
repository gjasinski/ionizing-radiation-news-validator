import unittest

from ionizing_radiation_news_validator.geocoding import Geocoding

"""
Run with PYTHONPATH=. python tests/test.py
"""


class TestGeocoding(unittest.TestCase):

    def test_distance(self):
        assert Geocoding.compute_distance_between_two_coordinates((20,30), (40,50)) > 0
        assert round(Geocoding.compute_distance_between_two_coordinates((20,30), (40,50))) == round(Geocoding.compute_distance_between_two_coordinates((20,30), (40,50)))
