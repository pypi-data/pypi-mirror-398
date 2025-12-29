import json
import os
from typing import Optional, Dict

current_dir = os.path.dirname(__file__)


class Locations:
    @staticmethod
    def countriesList() -> Dict:
        """Return a list of countries

        Returns:
            dict: Dictionary with available countries
        """
        countries_path = os.path.join(current_dir, "..", "assets", "countries.json")
        with open(countries_path) as countries_file:
            return json.load(countries_file)

    @staticmethod
    def statesList(country_code: str) -> Optional[Dict]:
        """Get states list by country ISO code

        Args:
            country_code (str): Input country code

        Returns:
            dict: Dictionary with available states if country_code exists
        """
        states_path = os.path.join(current_dir, "..", "assets", "states.json")
        with open(states_path) as states_file:
            states_dict = json.load(states_file)

            if country_code in states_dict:
                return states_dict[country_code]

        return None

    @staticmethod
    def formatsList(country_code: str) -> Optional[Dict]:
        """Get phone and zip formats list by country ISO code

        Args:
            country_code (str): Input country code

        Returns:
            dict: Dictionary with format data if country_code exists
        """
        formats_path = os.path.join(current_dir, "..", "assets", "formats.json")
        with open(formats_path) as formats_file:
            formats_dict = json.load(formats_file)

            if country_code in formats_dict:
                return formats_dict[country_code]

        return None
