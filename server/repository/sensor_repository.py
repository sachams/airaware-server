import datetime
import logging
from collections import defaultdict
from typing import List

from pydantic import TypeAdapter
from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app_config import outlier_threshold
from server.models import SensorDataModel, SiteModel
from server.repository.abstract_sensor_repository import AbstractSensorRepository
from server.schemas import (
    BreachSchema,
    HeatmapSchema,
    RankSchema,
    SensorDataCreateSchema,
    SensorDataSchema,
    SiteAverageSchema,
    SiteSchema,
)
from server.types import Classification, Frequency, Series, Source


class SensorRepository(AbstractSensorRepository):
    def __init__(self, session: Session):
        self.session = session

    def write_data(self, data: list[SensorDataCreateSchema]) -> None:
        """Writes Breathe London series data to the database"""
        objects = []
        for item in data:
            db_item = SensorDataModel(**item.model_dump())
            objects.append(db_item)
        self.session.bulk_save_objects(objects)

    def get_data(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        frequency: Frequency,
        codes: list[str] | None = None,
        types: list[Classification] | None = None,
    ) -> list[SensorDataSchema]:
        """Reads data from the datastore, averaging across the specified sites. If no
        sites are specified, it averages across all sites.
        """
        query = (
            select(
                func.date_trunc(frequency.value, SensorDataModel.time).label("time"),
                func.avg(SensorDataModel.value).label("value"),
            )
            .filter(SensorDataModel.series == series.name)
            .filter(SensorDataModel.time >= start)
            .filter(SensorDataModel.time < end)
        )

        # If we have been supplied a list of site codes or types, join with the Site table
        # and filter by site code and/or type
        if codes or types:
            query = query.join(SiteModel)

            if codes:
                query = query.filter(SiteModel.site_code.in_(codes))

            if types:
                query = query.filter(SiteModel.site_type.in_(types))

        query = query.group_by(
            func.date_trunc(frequency.value, SensorDataModel.time).label("time")
        ).order_by(func.date_trunc(frequency.value, SensorDataModel.time))

        SensorDataList = TypeAdapter(List[SensorDataSchema])
        return SensorDataList.validate_python(self.session.execute(query))

    def delete_data(self, series: Series, site_id: int) -> None:
        """Deletes data from the sensor repository for the specified site_id and series"""
        self.session.execute(
            delete(SensorDataModel)
            .where(SensorDataModel.site_id == site_id)
            .where(SensorDataModel.series == series)
        )

    def get_site_average(
        self, series: Series, start: datetime.datetime, end: datetime.datetime
    ) -> list[SiteAverageSchema]:
        """Reads data from the datastore, returning the average of all sites
        across the specified time period. Data is returned as list of site_code
        and average value.
        """
        query = (
            select(
                SiteModel.site_code.label("site_code"),
                func.avg(SensorDataModel.value).label("value"),
            )
            .join(SiteModel, SiteModel.site_id == SensorDataModel.site_id)
            .filter(SensorDataModel.series == series)
            .filter(SensorDataModel.time >= start)
            .filter(SensorDataModel.time < end)
            .group_by(SiteModel.site_code)
            .order_by(SiteModel.site_code)
        )

        site_averages = self.session.execute(query)
        SiteAveragesList = TypeAdapter(List[SiteAverageSchema])
        return SiteAveragesList.validate_python(site_averages)

    def get_latest_date(self, site_id: int, series: Series) -> datetime.datetime:
        reading = (
            self.session.execute(
                select(SensorDataModel)
                .filter(SensorDataModel.site_id == site_id)
                .filter(SensorDataModel.series == series)
                .order_by(desc(SensorDataModel.time))
                .limit(1)
            )
            .scalars()
            .first()
        )

        return None if reading is None else reading.time

    def get_sites(self, source: Source | None) -> list[SiteSchema]:
        """Returns the list of sites ordered by site code and optionally
        filtered by source"""
        query = select(SiteModel)
        if source is not None:
            query = query.filter(SiteModel.source == source)

        query = query.order_by(SiteModel.site_code)

        SiteList = TypeAdapter(List[SiteSchema])
        return SiteList.validate_python(self.session.execute(query).scalars())

    def get_site(self, site_code: str) -> SiteSchema:
        """Returns a single site object"""
        site = (
            self.session.execute(
                select(SiteModel).filter(SiteModel.site_code == site_code)
            )
            .scalars()
            .one_or_none()
        )

        if site is None:
            return None

        return SiteSchema.model_validate(site)

    def update_sites(self, sites: list[SiteSchema]) -> None:
        """Updates sites on the repository (matched by site_code)
        or adds new ones if they don't exist"""

        logging.info("Saving site list to database")
        for site in sites:
            existing_site = (
                self.session.execute(
                    select(SiteModel).filter(SiteModel.site_code == site.site_code)
                )
                .scalars()
                .one_or_none()
            )

            new_obj = SiteModel(**site.model_dump())

            if existing_site is None:
                self.session.add(new_obj)
            else:
                new_obj.site_id = existing_site.site_id
                self.session.merge(new_obj)

    def get_heatmap(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> dict[str, HeatmapSchema]:
        """Gets heatmap data for the specified series by hour of day and day of week, for all
        sites.
        """
        query = (
            select(
                SiteModel.site_code,
                func.date_part("dow", SensorDataModel.time).label("day"),
                func.date_part("hour", SensorDataModel.time).label("hour"),
                func.avg(SensorDataModel.value).label("value"),
            )
            .filter(SensorDataModel.series == series.name)
            .filter(SensorDataModel.time >= start)
            .filter(SensorDataModel.time < end)
            .filter(SiteModel.is_enabled == True)
            .join(SiteModel, SiteModel.site_id == SensorDataModel.site_id)
            .group_by(SiteModel.site_code)
            .group_by(func.date_part("dow", SensorDataModel.time).label("day"))
            .group_by(func.date_part("hour", SensorDataModel.time).label("hour"))
            .order_by(SiteModel.site_code)
        )

        # Return a dict of heatmap data, keyed by site_code
        result = self.session.execute(query)
        data = defaultdict(list)
        for row in result:
            data[row.site_code].append(
                HeatmapSchema(hour=row.hour, day=row.day, value=row.value)
            )

        return data

    def get_breach(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        threshold: float,
    ) -> dict[str, BreachSchema]:
        """Gets the number of days the daily average is above the speficied threshold for each
        site.
        """
        daily_avg_subquery = (
            select(
                SiteModel.site_code,
                func.date_trunc("day", SensorDataModel.time).label("date"),
                func.avg(SensorDataModel.value).label("average"),
            )
            .join(SiteModel, SiteModel.site_id == SensorDataModel.site_id)
            .filter(SensorDataModel.series == series.name)
            .filter(SensorDataModel.time >= start)
            .filter(SensorDataModel.time < end)
            .filter(SiteModel.is_enabled == True)
            .group_by(SiteModel.site_code)
            .group_by(func.date_trunc("day", SensorDataModel.time))
            .subquery()
        )

        breach_query = (
            select(
                daily_avg_subquery.c.site_code,
                func.count(daily_avg_subquery.c.date).label("count"),
            )
            .filter(daily_avg_subquery.c.average > threshold)
            .group_by(daily_avg_subquery.c.site_code)
            .order_by(daily_avg_subquery.c.site_code)
            .subquery()
        )

        breach_final_query = (
            select(SiteModel.site_code, breach_query.c.count)
            .join_from(
                SiteModel,
                breach_query,
                SiteModel.site_code == breach_query.c.site_code,
                isouter=True,
            )
            .filter(SiteModel.is_enabled == True)
        )

        ok_query = (
            select(
                daily_avg_subquery.c.site_code,
                func.count(daily_avg_subquery.c.date).label("count"),
            )
            .filter(daily_avg_subquery.c.average <= threshold)
            .group_by(daily_avg_subquery.c.site_code)
            .order_by(daily_avg_subquery.c.site_code)
            .subquery()
        )

        ok_final_query = (
            select(SiteModel.site_code, ok_query.c.count)
            .join_from(
                SiteModel,
                ok_query,
                SiteModel.site_code == ok_query.c.site_code,
                isouter=True,
            )
            .filter(SiteModel.is_enabled == True)
        )

        # Return a list of breach data, keyed by site_code
        total_days = (end - start).days
        # Make sure breach and ok fields are populated - they might not be if no values were
        # (not) breached
        data = defaultdict(lambda: defaultdict(int))

        result = self.session.execute(breach_final_query)
        for row in result:
            data[row.site_code]["breach"] = row.count if row.count is not None else 0

        result = self.session.execute(ok_final_query)
        for row in result:
            data[row.site_code]["ok"] = row.count if row.count is not None else 0

        for _, obj in data.items():
            # if "breach" not in obj:
            #     obj["breach"] = 0

            # if "ok" not in obj:
            #     obj["breach"] = 0

            obj["no_data"] = total_days - obj["breach"] - obj["ok"]

        return data

    def get_rank(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> dict[str, RankSchema]:
        """Gets the average over the period, and the rank of each site (1 = lowest)"""
        query = (
            select(
                SiteModel.site_code,
                func.avg(SensorDataModel.value).label("average"),
                func.row_number()
                .over(order_by=func.avg(SensorDataModel.value))
                .label("rank"),
            )
            .join(SiteModel)
            .filter(SensorDataModel.series == series.name)
            .filter(SensorDataModel.time >= start)
            .filter(SensorDataModel.time < end)
            .filter(SiteModel.is_enabled == True)
            .group_by(SiteModel.site_code)
        )

        # Return a dict of rank data, keyed by site_code
        result = self.session.execute(query)

        data = defaultdict(list)
        for row in result:
            data[row.site_code] = RankSchema(rank=row.rank, value=row.average)

        return data

    def get_outliers_threshold(
        self, series: Series
    ) -> dict[str, list[SensorDataSchema]]:
        """Returns arrays of outlier data for the specified series"""
        query = (
            select(SiteModel.site_code, SensorDataModel.value, SensorDataModel.time)
            .join(SiteModel, SiteModel.site_id == SensorDataModel.site_id)
            .filter(SensorDataModel.series == series.name)
            .filter(SensorDataModel.value > outlier_threshold[series.name])
            .filter(SiteModel.is_enabled == True)
            .order_by(SensorDataModel.time)
        )

        data = defaultdict(list)

        result = self.session.execute(query)
        for row in result:
            data[row.site_code].append(SensorDataSchema(time=row.time, value=row.value))

        return data
