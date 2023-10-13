import httpx
import os
import datetime
import json
import logging
import time

from borough_mapper import BoroughMapper


class BreatheLondon:
    def __init__(self, api_key):
        # Check if a directory called /data exists. If so, use it as the file root
        file_root = "/data" if os.path.isdir("/data") else "."
        self.max_retries = 3
        self.retry_pause = 1
        self.client = httpx.Client(timeout=30)
        self.api_key = api_key
        self.base_url = "https://api.breathelondon.org/api"

        self.site_cache_filename = f"{file_root}/site_cache.json"
        self.borough_mapper = BoroughMapper()

        with open(f"broken_sites.json", "r") as broken_sites_file:
            self.broken_sites = json.load(broken_sites_file)

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
                max_cache_age = datetime.datetime.utcnow() + datetime.timedelta(
                    minutes=-10
                )
                cache_modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(self.site_cache_filename)
                )
                logging.info(f"Cache last modified {cache_modified}")

                if cache_modified > max_cache_age:
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

    def _fix_status(self, status):
        match status:
            case "healthy":
                return "Healthy"

            case "offline":
                return "Offline"

            case "coming online":
                return "Coming online"

            case "needs attention" | "needsAttention":
                return "Needs attention"

            case _:
                return "Unknown"

    def _get_status_for_site(self, site_code, current_status):
        """Amends the site status if the site is on a broken list"""
        return "Needs attention" if site_code in self.broken_sites else current_status

    def get_sites(self):
        """Requests a list of sites from Breathe London and returns list of sites"""

        logging.info("Looking for cached site list")
        site_list = self._get_site_from_cache()
        if site_list is not None:
            return site_list

        logging.info("Loading site list from API")
        site_list = self._get("ListSensors")[0]

        for site in site_list:
            # # Tidy up SiteDescription
            # if site["SiteDescription"] is None:
            #     import pdb

            #     pdb.set_trace()

            # site["SiteDescription"] = None if "null" else site["SiteDescription"]

            # Add in borough name for each sensor
            site["Borough"] = self.borough_mapper.get_borough(
                site["Latitude"], site["Longitude"]
            )

            # Fix up status - both typos in the status, and also whether the node is on a list
            # of broken sites
            site["OverallStatus"] = self._get_status_for_site(
                site["SiteCode"], self._fix_status(site["OverallStatus"])
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
