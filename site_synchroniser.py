import datetime
import logging
import time

from server.schemas import SensorDataCreate
from server.types import Series


class SiteSynchroniser:
    def __init__(self, datastore, breathe_london):
        self.datastore = datastore
        self.sources = [breathe_london]

    def sync_all(self, resync, pause, start):
        """Syncs all sites and series from all sources to the datastore"""
        all_series = [Series.pm25, Series.no2]

        for source in self.sources:
            logging.info(f"*** Starting {source.name} sync ***")

            all_sites = source.get_sites(None)
            logging.info(f"Found {len(all_sites)} sites")

            for site in all_sites:
                if start is not None and site["SiteCode"] < start:
                    logging.info(f"Skipping site {site['SiteCode']}")
                    continue

                for series in all_series:
                    self.sync(site["SiteCode"], series, resync)
                    logging.info(f"Pausing for {pause}s")
                    time.sleep(pause)

            logging.info(f"*** {source.name} sync complete ***")

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

        latest_date = None if resync else self.datastore.get_latest_date(site_code, series)

        if latest_date is not None:
            logging.info(f"[{site_code}:{series}] Latest datastore date is {latest_date}")
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
            data_schema = []
            for item in data:
                if item["ScaledValue"] is None:
                    logging.warning(
                        f"[{site_code}:{series}] Found null data for timestamp {item['DateTime']} - skipping"
                    )
                    continue

                obj = SensorDataCreate(
                    time=datetime.datetime.strptime(item["DateTime"], "%Y-%m-%dT%H:%M:%S.000Z"),
                    value=item["ScaledValue"],
                )
                data_schema.append(obj)

            logging.info(f"[{site_code}:{series}] Writing data to datastore")
            self.datastore.write_data(site_code, series, data_schema)
            logging.info(f"[{site_code}:{series}] Data written to datastore")

        logging.info(f"[{site_code}:{series}] Sync complete")
