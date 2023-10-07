import httpx
import os
import datetime
import json
import logging
import time

from borough_mapper import BoroughMapper


class BreatheLondon:
    def __init__(self, api_key):
        self.max_retries = 3
        self.retry_pause = 1
        self.client = httpx.Client(timeout=30)
        self.api_key = api_key
        self.base_url = "https://api.breathelondon.org/api"
        self.site_cache_filename = "/data/site_cache.json"
        self.borough_mapper = BoroughMapper()

    def _get(self, endpoint):
        """Makes a GET request from the endpoint"""
        params = {"key": self.api_key}
        url = f"{self.base_url}/{endpoint}"

        retry_count = 0
        while True:
            try:
                response = self.client.get(url, params=params)
                return response.json()
            except httpx.HTTPError as e:
                if retry_count >= self.max_retries:
                    logging.error(
                        f"Caught exception while requesting data from API: {str(e)}. Retry limit reached"
                    )
                    raise

                retry_count += 1
                logging.warning(f"{str(e)}. Pausing {self.retry_pause}s before retry")
                time.sleep(self.retry_pause)

    def _get_site_from_cache(self):
        try:
            if os.path.exists(self.site_cache_filename):
                logging.info(f"Found site cache at {self.site_cache_filename}")
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
        logging.info(f"Saving site list to cache at {self.site_cache_filename}")
        try:
            with open(self.site_cache_filename, "w") as cache:
                json.dump(site_list, cache)
        except FileNotFoundError:
            logging.warning("Unable to save sites to cache")

    def get_sites(self):
        """Requests a list of sites from Breathe London and returns list of sites"""

        logging.info("Looking for cached site list")
        site_list = self._get_site_from_cache()
        if site_list is not None:
            return site_list

        logging.info("Loading site list from API")
        site_list = self._get("ListSensors")[0]

        # Add in borough name for each sensor
        for site in site_list:
            site["Borough"] = self.borough_mapper.get_borough(
                site["Latitude"], site["Longitude"]
            )

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
