import datetime
import logging
import time
from collections import defaultdict

from app_config import daily_limits
from server.schemas import (
    OutlierBlockSchema,
    RangeSchema,
    SensorDataCreateSchema,
    SensorDataSchema,
    SiteAverageSchema,
    SiteSchema,
    SyncSiteSchema,
    WrappedSchema,
)
from server.service.processing_result import ProcessingResult
from server.source.remote_sources import RemoteSources
from server.types import Classification, Frequency, Series, Source
from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork
from server.utils import round_datetime_to_day


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
        enrich: bool = False,
    ) -> list[SiteAverageSchema]:
        with uow:
            averages = uow.sensors.get_site_average(series, start, end)
            if enrich:
                # Enrich the data with site details
                sites = uow.sensors.get_sites(None)
                site_map = {site.site_code: site for site in sites}
                for average in averages:
                    average.site_details = site_map.get(average.site_code)

            return ProcessingResult.SUCCESS_RETRIEVED, averages

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
    def resync_data(
        uow: AbstractUnitOfWork, data: SyncSiteSchema
    ) -> tuple[ProcessingResult, str | None]:
        """Reads site information from all sources and inserts/updates records in the repository.
        Note that the site_code field is used as the unique identifier for updates."""
        try:
            with uow:
                site = uow.sensors.get_site(data.site_code)

            if site is None:
                logging.error(f"Unable to find site {data.site_code}")
                return (
                    ProcessingResult.ERROR_NOT_FOUND,
                    f"Unable to find site {data.site_code}",
                )

            SensorService.sync_single_site_data(
                uow, data.site_code, None, site.source, data.series, True
            )
            return ProcessingResult.SUCCESS_UPDATED, None
        except Exception as e:
            logging.exception(f"Caught exception while resyncing data: {e}")
            return ProcessingResult.ERROR_INTERNAL_SERVER_ERROR, e

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
    def get_outliers_in_context(
        uow: AbstractUnitOfWork,
        series: Series,
    ) -> list[dict]:
        with uow:
            # 1. Generate outliers for each outlier calculation method (at the moment
            # we only have threshold) into a dict keyed by site_code
            logging.info("Querying for outlier data")
            outliers_by_method = {
                "threshold": uow.sensors.get_outliers_threshold(series)
            }
            outliers_by_site_code = SensorService.reshape_outliers_by_site_code(
                outliers_by_method
            )

            # 2. For each site code, get outliers in context
            outliers_in_context = {}
            for site_code, outliers in outliers_by_site_code.items():
                outliers_in_context[site_code] = (
                    SensorService.get_outliers_in_context_for_site(
                        uow, outliers, site_code, series
                    )
                )

            reshaped_data = []
            for site_code, outliers in outliers_in_context.items():
                reshaped_data.append({"site_code": site_code, "outliers": outliers})

            return ProcessingResult.SUCCESS_RETRIEVED, reshaped_data

    @staticmethod
    def get_outliers_in_context_for_site(
        uow: AbstractUnitOfWork,
        outliers_by_method: dict[str, list[SensorDataSchema]],
        site_code: str,
        series: Series,
    ) -> list[OutlierBlockSchema]:
        """Generates and returns data that are considered outliers, along with
        context (all data points for +/- 1 day)"""

        # 1. For each outlier calculation method results, calculate a list of
        # blocks (ranges) for the data. It's fine to have one big list of blocks
        # that might overlap, because we will merge them anyway
        logging.info("Calculating block ranges")
        blocks = []
        for _, data in outliers_by_method.items():
            blocks += SensorService.get_block_ranges(data)

        # 2. Extend each block by a day either side (gives more context when viewing
        # data)
        logging.info("Extending blocks")
        extended_blocks = SensorService.extend_blocks(blocks)

        # 3. Merge any overlapping blocks (note, this will also sort)
        logging.info("Merging blocks")
        merged_blocks = SensorService.merge_blocks(extended_blocks)

        # 4. We now have a list of blocks, and each block will have outliers
        # from at least one calculation method. Go through each block and see
        # which outlier data can be assigned to that block
        logging.info("Assigning outlier data to blocks")
        outlier_blocks: list[OutlierBlockSchema] = []

        for merged_block in merged_blocks:
            # Create a block with all outlier data and context data
            outlier_block = OutlierBlockSchema(site_code=site_code, range=merged_block)

            # Query context (ie, normal data) for this block
            logging.info(
                f"Adding context to block {merged_block.start.isoformat()}"
                f"-{merged_block.end.isoformat()}"
            )
            outlier_block.context_data = uow.sensors.get_data(
                series,
                merged_block.start,
                merged_block.end,
                Frequency.hour,
                [site_code],
            )

            # Go through outlier data and assign any points that fall
            # within the limits of this block
            logging.info(
                f"Assigning outlier data to block {merged_block.start.isoformat()}"
                f"-{merged_block.end.isoformat()}"
            )
            for outlier_method, outlier_data in outliers_by_method.items():
                while (
                    outlier_data
                    and outlier_data[0].time >= merged_block.start
                    and outlier_data[0].time < merged_block.end
                ):
                    outlier_block.outlier_data[outlier_method].append(
                        outlier_data.pop(0)
                    )

            outlier_blocks.append(outlier_block)

        return outlier_blocks

    @staticmethod
    def reshape_outliers_by_site_code(
        outliers_by_method: dict[str, dict[str, list[SensorDataSchema]]],
    ) -> dict[str, dict[str, list[SensorDataSchema]]]:
        """Takes a dict that looks like this:

        {
            "threshold": {"site1": [SensorDataSchema1, SensorDataSchema2],
                          "site2": [SensorDataSchema3, SensorDataSchema4]},
            "z_score":   {"site1": [SensorDataSchema5, SensorDataSchema6],
                          "site2": [SensorDataSchema7, SensorDataSchema8]},
        }

        and reshapes it to look like this:
        {
            "site1": {"threshold": [SensorDataSchema1, SensorDataSchema2],
                      "z_score":   [SensorDataSchema5, SensorDataSchema6]},
            "site2": {"threshold": [SensorDataSchema3, SensorDataSchema4],
                      "z_score":   [SensorDataSchema7, SensorDataSchema8]},
        }
        """

        outliers_by_site_code = defaultdict(dict)

        for method, sites in outliers_by_method.items():
            for site_code, site_data in sites.items():
                outliers_by_site_code[site_code][method] = site_data

        return outliers_by_site_code

    @staticmethod
    def merge_blocks(source: list[RangeSchema]) -> list[RangeSchema]:
        """Merges a list of ranges so that there are no overlapping blocks"""
        if len(source) == 0:
            return []

        source.sort(key=lambda entry: entry.start)

        merged = []

        merged.append(source[0])

        for block in source[1:]:
            # Check for overlapping interval,
            # if interval overlap
            if merged[-1].start <= block.start <= merged[-1].end:
                merged[-1].end = max(merged[-1].end, block.end)
            else:
                merged.append(block)

        return merged

    @staticmethod
    def extend_blocks(source: list[RangeSchema]) -> list[RangeSchema]:
        """Extends each block by adding a day each side, and rounding down (start) and up (end)
        so that each block starts and ends at midnight"""
        extended = [
            RangeSchema(
                start=round_datetime_to_day(
                    block.start - datetime.timedelta(days=1), True
                ),
                end=round_datetime_to_day(
                    block.end + datetime.timedelta(days=1), False
                ),
            )
            for block in source
        ]

        return extended

    @staticmethod
    def get_block_ranges(outliers: list[SensorDataSchema]) -> list[RangeSchema]:
        """Calculates date blocks from the outlier data. An outlier range is defined as any
        series of outlier points that are no more than a day apart."""
        if not outliers:
            return []

        block_ranges = []

        start = outliers[0].time
        for index, row in enumerate(outliers):
            # Grab the next row, if we can
            next_row = outliers[index + 1] if index < len(outliers) - 1 else None

            if next_row:
                if next_row.time - row.time > datetime.timedelta(days=1):
                    # The next row is more than a day away - close out this block
                    block_ranges.append(RangeSchema(start=start, end=row.time))
                    start = next_row.time
            else:
                # No more next row - close out the block
                block_ranges.append(RangeSchema(start=start, end=row.time))

        return block_ranges
