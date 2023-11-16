import datetime
import logging
import time

from server.schemas import SensorDataSchema, SiteAverageSchema, SiteSchema
from server.service.processing_result import ProcessingResult
from server.source.remote_sources import RemoteSources
from server.types import Frequency, Series, Source
from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork


def get_data(
    uow: AbstractUnitOfWork,
    series: Series,
    start: datetime.datetime,
    end: datetime.datetime,
    frequency: Frequency,
    codes: list[str],
) -> list[SensorDataSchema]:
    with uow:
        items = uow.sensors.get_data(series, start, end, frequency, codes)
        return ProcessingResult.SUCCESS_RETRIEVED, items


def get_site_average(
    uow: AbstractUnitOfWork,
    series: Series,
    start: datetime.datetime,
    end: datetime.datetime,
) -> list[SiteAverageSchema]:
    with uow:
        items = uow.sensors.get_site_average(series, start, end)
        return ProcessingResult.SUCCESS_RETRIEVED, items


def get_sites(uow: AbstractUnitOfWork, source: Source | None) -> list[SiteSchema]:
    with uow:
        sites = uow.sensors.get_sites(source)
        return ProcessingResult.SUCCESS_RETRIEVED, sites


def sync_sites(uow: AbstractUnitOfWork) -> None:
    """Reads site information from all sources and inserts/updates records in the repository.
    Note that the site_code field is used as the unique identifier for updates."""
    for source in Source:
        remote_source = RemoteSources().get_source(source)

        with uow:
            sites = remote_source.get_sites()
            uow.sensors.update_sites(sites)

        return ProcessingResult.SUCCESS_RETRIEVED, None


def sync_single_site_data(
    uow: AbstractUnitOfWork, code: str, source: Source, series: Series, resync: bool
):
    with uow:
        """SYnchronises data from a source to the datastore by:
        1. looking for the latest data in the datastore
        2. Reading data from the source after this date
        3. Writing this data to the datastore
        """
        logging.info(f"[{code}:{series}] {'Resync' if resync else 'Sync'} Sync started")

        # Get the source of data based on the source enum
        remote_source = RemoteSources().get_source(source)

        # Work out when the last data in our database is
        latest_date = None if resync else uow.sensors.get_latest_date(code, series)

        if latest_date is not None:
            logging.info(f"[{code}:{series}] Latest repository date is {latest_date}")
        else:
            logging.info(
                f"[{code}:{series}] No data present in repository or full resync triggered - "
                "loading from 1 Jan 2000"
            )
            latest_date = datetime.datetime(2000, 1, 1)

        # We want to start from the next point after the latest date
        start = latest_date + datetime.timedelta(hours=1)
        end = datetime.datetime.utcnow()

        logging.info(f"[{code}:{series}] Loading data from {source} between {start} and {end}")

        start_time = time.time()
        data = remote_source.get_sensor_data(code, start, end, series)
        elapsed = time.time() - start_time

        logging.info(f"[{code}:{series}] Found {len(data)} rows in {elapsed:.3f}s")

        start_time = time.time()
        uow.sensors.write_data(data)
        elapsed = time.time() - start_time

        logging.info(f"[{code}:{series}] Data written to repository in {elapsed:.3f}s")

        logging.info(f"[{code}:{series}] Sync complete")


def sync_all(uow: AbstractUnitOfWork, resync: bool, start_code: str):
    """Syncs all sites and series from all sources to the datastore. Note that it takes the list
    of sites from the database, so assumes that this has been synced first"""
    sites = uow.sensors.get_sites()

    for site in sites:
        # Skip over sites before `start_code` - makes it easy to resume a failed
        # sync when testing
        if start_code is not None and site.code < start_code:
            logging.info(f"Skipping site {site.code}")
            continue

        logging.info(f"*** Starting {site.code} sync ***")

        for series in Series:
            sync_single_site_data(uow, site.code, site.source, series, resync)

        logging.info(f"*** {site.code} sync complete ***")
