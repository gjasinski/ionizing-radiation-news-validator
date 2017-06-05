import unittest

from ionizing_radiation_news_validator.geocoding import Geocoding
from ionizing_radiation_news_validator.nlp_news_checker import NLPNewsChecker
from ionizing_radiation_news_validator.radiation_checking_tool import RadiationCheckingTool
"""
Run with PYTHONPATH=. python tests/test.py
"""


class TestGeocoding(unittest.TestCase):

    def test_distance(self):
        assert Geocoding.compute_distance_between_two_coordinates((20, 30), (40, 50)) > 0
        assert round(Geocoding.compute_distance_between_two_coordinates((20, 30), (40, 50))) == round(Geocoding.compute_distance_between_two_coordinates((20, 30), (40, 50)))

    def test_get_city_coords(self):
        g = Geocoding()
        (coord1, coord2) = g.get_city_coords("Warsaw")
        assert (round(coord1), round(coord2)) == (52, 21)

    def test_get_capital_city_by_country(self):
        g = Geocoding()
        assert g.get_capital_city_by_country("Poland") == "Warsaw"

    def test_nlp_results(self):
        news1 = "http://www.mirror.co.uk/science/nuclear-radiation-been-spreading-across-9861177"
        nlp_news1 = NLPNewsChecker(news1)
        nlp_news1.get_article_date()
        nlp_news1.find_countries_named_in_article()
        assert nlp_news1.date
        assert nlp_news1.enumerated_countries != []
        assert "Poland" in nlp_news1.enumerated_countries

    def test_new_date(self):
        date = "2017-01-01"
        rct = RadiationCheckingTool()
        rct.set_up_date(date)
        assert rct._RadiationCheckingTool__date == date
        rct.set_up_date("01-01-2017")
        assert rct._RadiationCheckingTool__date == date
