import datetime
import logging
import time


class SiteSynchroniser:
    def __init__(self, datastore, breathe_london):
        self.datastore = datastore
        self.breathe_london = breathe_london

    def sync_all(self, resync, pause, start):
        """Syncs all sites and series from BreatheLondon to the datastore"""
        logging.info("Loading all sites from BreatheLondon")
        all_sites = self.breathe_london.get_sites()[0]
        logging.info(f"Found {len(all_sites)} sites")

        all_series = ["PM25", "NO2"]

        for site in all_sites:
            if start is not None and site["SiteCode"] < start:
                logging.info(f"Skipping site {site['SiteCode']}")
                continue

            for series in all_series:
                self.sync(site["SiteCode"], series, resync)
                logging.info(f"Pausing for {pause}s")
                time.sleep(pause)

    def sync(self, site_code, series, resync):
        """SYnchronises data from BL to the datastore by:
        1. looking for the latest data in the datastore
        2. Reading data from BL after this date
        3. Writing this data to the datastore
        """
        if resync:
            logging.info(f"[{site_code}:{series}] Resync started")
        else:
            logging.info(f"[{site_code}:{series}] Sync started")

        latest_date = (
            None if resync else self.datastore.get_latest_date(site_code, series)
        )

        if latest_date is not None:
            logging.info(
                f"[{site_code}:{series}] Latest datastore date is {latest_date}"
            )
        else:
            logging.info(
                f"[{site_code}:{series}] No data present in datastore or full resync triggered - loading from dawn of time"
            )
            latest_date = datetime.datetime(2000, 1, 1)

        # We want to start from the next point after the latest date
        start = latest_date + datetime.timedelta(hours=1)
        end = datetime.datetime.utcnow()

        logging.info(
            f"[{site_code}:{series}] Loading data from BreatheLondon between {start} and {end}"
        )

        data = self.breathe_london.get_sensor_data(site_code, start, end, series)

        logging.info(f"[{site_code}:{series}] Found {len(data)} rows")

        if data:
            logging.info(f"[{site_code}:{series}] Writing data to datastore")
            self.datastore.write_data(series, data)
            logging.info(f"[{site_code}:{series}] Data written to datastore")

        logging.info(f"[{site_code}:{series}] Sync complete")
