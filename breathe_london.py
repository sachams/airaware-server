import httpx
import os
import datetime
import json
import logging


class BreatheLondon:
    def __init__(self, api_key):
        self.client = httpx.Client(timeout=60)
        self.api_key = api_key
        self.base_url = "https://api.breathelondon.org/api"
        self.site_cache_filename = "site_cache.json"

    def _get(self, endpoint):
        """Makes a GET request from the endpoint"""
        params = {"key": self.api_key}
        url = f"{self.base_url}/{endpoint}"
        response = self.client.get(url, params=params)
        return response.json()

    def _get_site_from_cache(self):
        try:
            if os.path.exists(self.site_cache_filename):
                logging.info(f"Found site cache")
                one_day_ago = datetime.datetime.utcnow() + datetime.timedelta(days=-1)
                cache_modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(self.site_cache_filename)
                )
                logging.info(f"Cache last modified {cache_modified}")

                if cache_modified > one_day_ago:
                    logging.info("Loading site list from cache")
                    with open(self.site_cache_filename, "r") as cache:
                        site_list = json.load(cache)
                        return site_list
        except json.JSONDecodeError as e:
            return None

        return None

    def _save_site_cache(self, site_list):
        logging.info("Saving site list to cache")
        with open(self.site_cache_filename, "w") as cache:
            json.dump(site_list, cache)

    def get_sites(self):
        """Requests a list of sites from Breathe London and returns list of sites"""

        logging.info("Looking for cached site list")
        site_list = self._get_site_from_cache()
        if site_list is not None:
            return site_list

        logging.info("Loading site list from API")
        site_list = self._get("ListSensors")

        self._save_site_cache(site_list)

        return site_list

    @staticmethod
    def _isoformat_utc(dt):
        # The normal datetime.isoformat() doesn't include the timezone (Z = UTC)
        # so add this now
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_sensor_data(self, site_code, start, end, series):
        data = self._get(
            f"getClarityData/{site_code}/"
            f"I{series}/"
            f"{BreatheLondon._isoformat_utc(start)}/"
            f"{BreatheLondon._isoformat_utc(end)}/"
            "Hourly"
        )

        if type(data) == dict:
            # Looks like we get the following returned if there's no data:
            # {
            #     "recordsets": [],
            #     "output": {},
            #     "rowsAffected": [
            #         1,
            #         1,
            #         1,
            #         1
            #     ],
            #     "returnValue": 0
            # }            
            return []
        
        return data