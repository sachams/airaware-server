import logging
import pyarrow as pa
import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased
from sqlalchemy import desc, select

from . import models, schemas


class PostgresDatastore:
    def __init__(self, db: Session):
        self.db = db

    def write_request_log(self, url: str, ip_address: str):
        """Records requests"""
        db_item = models.RequestLog(
            path=url, ip_address=ip_address, time=datetime.datetime.utcnow()
        )
        self.db.add(db_item)
        self.db.commit()

    def write_data(self, site_code, series, data: list[schemas.SensorDataCreate]):
        """Writes Breathe London series data to the database"""
        objects = []
        for item in data:
            db_item = models.SensorData(
                site_code=site_code, series=series, time=item.time, value=item.value
            )
            objects.append(db_item)
        self.db.bulk_save_objects(objects)
        self.db.commit()

    def read_data(self, series, start, end, site_codes, frequency):
        """Reads data from the datastore, averaging across the specified sites. If no
        sites are specified, it averages across all sites.

        site_codes: a list of sites to average over. If empty, it averages over all
                    sites.
        frequency:  either `hourly` or `daily`
        """
        frequency_mapper = {"hourly": "hour", "daily": "day"}
        db_frequency = frequency_mapper.get(frequency)
        if db_frequency is None:
            raise Exception(f"Unknown frequency {frequency}")

        query = (
            select(
                func.date_trunc(db_frequency, models.SensorData.time).label("time"),
                func.avg(models.SensorData.value).label("value"),
            )
            .filter(models.SensorData.series == series)
            .filter(models.SensorData.time >= start)
            .filter(models.SensorData.time < end)
        )

        if site_codes:
            query = query.filter(models.SensorData.site_code.in_(site_codes))

        query = query.group_by(
            func.date_trunc(db_frequency, models.SensorData.time).label("time")
        ).order_by(func.date_trunc(db_frequency, models.SensorData.time))

        return self.db.execute(query)

    def read_site_average(self, series, start, end) -> list[tuple[str, float]]:
        """Reads data from the datastore, returning the average of all sites
        across the specified time period. Data is returned as list of site_code
        and average value.
        """
        return self.db.execute(
            select(
                models.SensorData.site_code,
                func.avg(models.SensorData.value).label("value"),
            )
            .filter(models.SensorData.series == series)
            .filter(models.SensorData.time >= start)
            .filter(models.SensorData.time < end)
            .group_by(models.SensorData.site_code)
            .order_by(models.SensorData.site_code)
        )

    def get_latest_date(self, site_code, series) -> datetime.datetime:
        reading = (
            self.db.execute(
                select(models.SensorData)
                .filter(models.SensorData.site_code == site_code)
                .filter(models.SensorData.series == series)
                .order_by(desc(models.SensorData.time))
                .limit(1)
            )
            .scalars()
            .first()
        )

        return None if reading is None else reading.time
