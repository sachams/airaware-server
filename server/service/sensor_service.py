import datetime
import logging
import time

from app_config import daily_limits
from server.schemas import (
    BadDataSchema,
    SensorDataCreateSchema,
    SensorDataSchema,
    SiteAverageSchema,
    SiteSchema,
    WrappedSchema,
)
from server.service.processing_result import ProcessingResult
from server.source.remote_sources import RemoteSources
from server.types import Classification, Frequency, Series, Source
from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork


class SensorService:
    @staticmethod
    def get_data(
        uow: AbstractUnitOfWork,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        frequency: Frequency,
        codes: list[str],
        types: list[Classification],
    ) -> list[SensorDataSchema]:
        with uow:
            items = uow.sensors.get_data(series, start, end, frequency, codes, types)
            return ProcessingResult.SUCCESS_RETRIEVED, items

    @staticmethod
    def get_site_average(
        uow: AbstractUnitOfWork,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> list[SiteAverageSchema]:
        with uow:
            items = uow.sensors.get_site_average(series, start, end)
            return ProcessingResult.SUCCESS_RETRIEVED, items

    @staticmethod
    def get_sites(uow: AbstractUnitOfWork, source: Source | None) -> list[SiteSchema]:
        with uow:
            sites = uow.sensors.get_sites(source)
            return ProcessingResult.SUCCESS_RETRIEVED, sites

    @staticmethod
    def get_site(uow: AbstractUnitOfWork, site_code: str) -> SiteSchema:
        """Returns a single site object"""
        with uow:
            site = uow.sensors.get_site(site_code)
            return ProcessingResult.SUCCESS_RETRIEVED, site

    @staticmethod
    def sync_sites(uow: AbstractUnitOfWork) -> None:
        """Reads site information from all sources and inserts/updates records in the repository.
        Note that the site_code field is used as the unique identifier for updates."""
        for source in Source:
            remote_source = RemoteSources().get_source(source)

            with uow:
                sites = remote_source.get_sites()
                uow.sensors.update_sites(sites)
                uow.commit()

            return ProcessingResult.SUCCESS_RETRIEVED, None

    @staticmethod
    def sync_single_site_data(
        uow: AbstractUnitOfWork,
        site_code: str,
        site_id: int | None,
        source: Source,
        series: Series,
        resync: bool,
    ):
        with uow:
            """Synchronises data from a source to the datastore by:
            1. looking for the latest data in the datastore
            2. Reading data from the source after this date
            3. Writing this data to the datastore
            """
            logging.info(
                f"[{site_code}:{series}] {'Resync' if resync else 'Sync'} started"
            )

            if site_id is None:
                site = uow.sensors.get_site(site_code)
                if site is None:
                    raise Exception(
                        f"Unable to find site {site_code} in the repository. Has it been synced yet?"
                    )

                site_id = site.site_id

            # Get the source of data based on the source enum
            remote_source = RemoteSources().get_source(source)

            # If we're doing a resync, delete existing data for this site
            if resync:
                logging.info(
                    f"[{site_code}:{series}] Deleting existing data due to resync"
                )
                uow.sensors.delete_data(series, site_id)
                latest_date = datetime.datetime(2000, 1, 1)
            else:
                # Work out when the last data in our database is
                latest_date = uow.sensors.get_latest_date(site_id, series)

                if latest_date is not None:
                    logging.info(
                        f"[{site_code}:{series}] Date of most recent data in repository is {latest_date}"
                    )
                else:
                    logging.info(
                        f"[{site_code}:{series}] No data present in repository - "
                        "loading from 1 Jan 2000"
                    )
                    latest_date = datetime.datetime(2000, 1, 1)

            # We want to start from the next point after the latest date
            start = latest_date + datetime.timedelta(hours=1)
            end = datetime.datetime.utcnow()

            logging.info(
                f"[{site_code}:{series}] Loading data from {source} between {start} and {end}"
            )

            start_time = time.time()
            data = remote_source.get_sensor_data(site_code, start, end, series)
            elapsed = time.time() - start_time

            logging.info(
                f"[{site_code}:{series}] Found {len(data)} rows in {elapsed:.3f}s"
            )

            # We need to add in the site code and series on each record
            enriched = [
                SensorDataCreateSchema(
                    **item.model_dump(), site_id=site_id, series=series
                )
                for item in data
            ]
            start_time = time.time()
            uow.sensors.write_data(enriched)
            uow.commit()
            elapsed = time.time() - start_time

            logging.info(
                f"[{site_code}:{series}] Data written to repository in {elapsed:.3f}s"
            )

            logging.info(f"[{site_code}:{series}] Sync complete")

    @staticmethod
    def sync_all(uow: AbstractUnitOfWork, resync: bool, start_code: str):
        """Syncs all sites and series from all sources to the datastore. Note that it takes the list
        of sites from the database, so assumes that this has been synced first"""
        with uow:
            sites = uow.sensors.get_sites(None)

        # This block is outside the context handler as sync_single_site_data will enter uow context
        # handler itself
        for site in sites:
            # Skip over sites before `start_code` - makes it easy to resume a failed
            # sync when testing
            if start_code is not None and site.site_code < start_code:
                logging.info(f"Skipping site {site.site_code}")
                continue

            logging.info(f"*** Starting {site.site_code} sync ***")

            for series in Series:
                SensorService.sync_single_site_data(
                    uow, site.site_code, site.site_id, site.source, series, resync
                )

            logging.info(f"*** {site.site_code} sync complete ***")

    @staticmethod
    def generate_wrapped(uow: AbstractUnitOfWork, year: int) -> list[WrappedSchema]:
        """Generates and returns a dict of summary statistics for the given year"""
        with uow:
            start = datetime.datetime(year, 1, 1)
            end = datetime.datetime(year + 1, 1, 1)

            logging.info(f"*** Starting wrapped generation for {year}")

            # Load site data - only load enabled sites
            logging.info("Loading site data")
            sites = list(filter(lambda x: x.is_enabled, uow.sensors.get_sites(None)))

            # Load heatmap data
            logging.info("Generating heatmap data")
            heatmap_data_pm25 = uow.sensors.get_heatmap(Series.pm25, start, end)
            heatmap_data_no2 = uow.sensors.get_heatmap(Series.no2, start, end)

            # Load breach data
            logging.info("Generating breach data")
            breach_data_pm25 = uow.sensors.get_breach(
                Series.pm25, start, end, daily_limits["pm25"]["who"]
            )
            breach_data_no2 = uow.sensors.get_breach(
                Series.no2, start, end, daily_limits["no2"]["who"]
            )

            # Load rank data
            logging.info("Generating rank data")
            rank_data_pm25 = uow.sensors.get_rank(Series.pm25, start, end)
            rank_data_no2 = uow.sensors.get_rank(Series.no2, start, end)

            # Now let's mash it all together. The end result is a list of objects, one for each
            # site, that contains the data for that site. We'll build it up as a dict as that's
            # a bit easier, and then convert it to a list.
            logging.info("Reformatting data")
            data = {
                site.site_code: {
                    "details": site,
                    "heatmap": {"pm25": [], "no2": []},
                    "breach": {},
                    "rank": {},
                }
                for site in sites
            }

            # Append heatmap data
            for site_code, values in heatmap_data_pm25.items():
                data[site_code]["heatmap"]["pm25"] = values

            for site_code, values in heatmap_data_no2.items():
                data[site_code]["heatmap"]["no2"] = values

            # Append breach data
            for site_code, values in breach_data_pm25.items():
                data[site_code]["breach"]["pm25"] = values

            for site_code, values in breach_data_no2.items():
                data[site_code]["breach"]["no2"] = values

            # Append rank data
            for site_code, values in rank_data_pm25.items():
                data[site_code]["rank"]["pm25"] = values

            for site_code, values in rank_data_no2.items():
                data[site_code]["rank"]["no2"] = values

            # Finally convert to a list of WrappedSchema objects and return
            data_list = [
                WrappedSchema(
                    details=obj["details"],
                    heatmap=obj["heatmap"],
                    breach=obj["breach"],
                    rank=obj["rank"],
                )
                for _, obj in data.items()
            ]

            logging.info("*** Wrapped generation complete")

            return ProcessingResult.SUCCESS_RETRIEVED, data_list

    @staticmethod
    def get_bad_data(uow: AbstractUnitOfWork) -> list[BadDataSchema]:
        """Generates and returns a dict of summary statistics for the given year"""
        with uow:
            logging.info("Querying for bad data")

            bad_data = uow.sensors.get_bad_data()
