import datetime
import logging
from typing import List

from pydantic import TypeAdapter
from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from server.models import SensorDataModel, SiteModel
from server.repository.abstract_sensor_repository import AbstractSensorRepository
from server.schemas import (
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
        codes: list[str] | None,
        types: list[Classification] | None,
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
