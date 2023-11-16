import datetime
from typing import List

from pydantic import TypeAdapter
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from server.models import SensorDataModel, SiteModel
from server.repository.abstract_sensor_repository import AbstractSensorRepository
from server.schemas import SensorDataCreateSchema, SensorDataSchema, SiteAverageSchema, SiteSchema
from server.types import Frequency, Series, Source


class SensorRepository(AbstractSensorRepository):
    def __init__(self, session: Session):
        self.session = session

    def write_data(self, data: list[SensorDataCreateSchema]) -> None:
        """Writes Breathe London series data to the database"""
        objects = []
        for item in data:
            db_item = SensorDataModel(**item.model_dump())
            objects.append(db_item)
        self.db.bulk_save_objects(objects)
        self.db.commit()

    def get_data(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        frequency: Frequency,
        codes: list[str] | None,
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

        # If we have been supplied a list of site codes, join with the Site table
        # and filter by site code
        if codes:
            query = query.join(SiteModel).filter(SiteModel.code.in_(codes))

        query = query.group_by(
            func.date_trunc(frequency.value, SensorDataModel.time).label("time")
        ).order_by(func.date_trunc(frequency.value, SensorDataModel.time))

        SensorDataList = TypeAdapter(List[SensorDataSchema])
        return SensorDataList.validate_python(self.db.execute(query))

    def get_site_average(
        self, series: Series, start: datetime.datetime, end: datetime.datetime
    ) -> list[SiteAverageSchema]:
        """Reads data from the datastore, returning the average of all sites
        across the specified time period. Data is returned as list of site_code
        and average value.
        """
        return self.db.execute(
            select(
                SensorDataModel.site_code,
                func.avg(SensorDataModel.value).label("value"),
            )
            .filter(SensorDataModel.series == series)
            .filter(SensorDataModel.time >= start)
            .filter(SensorDataModel.time < end)
            .group_by(SensorDataModel.site_code)
            .order_by(SensorDataModel.site_code)
        )

    def get_latest_date(self, site_code, series) -> datetime.datetime:
        reading = (
            self.db.execute(
                select(SensorDataModel)
                .filter(SensorDataModel.site_code == site_code)
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

        query = query.order_by(desc(SiteModel.code))
        SiteList = TypeAdapter(List[SiteSchema])
        return SiteList.validate_python(self.db.execute(query))

    def update_sites(self, list[SiteSchema]) -> None:
        """Updates sites on the repository (matched by site_code) or adds new ones if they don't exist"""
        # TODO: add code
        pass
