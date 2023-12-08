import abc
import datetime

from server.schemas import (
    SensorDataCreateSchema,
    SensorDataSchema,
    SiteAverageSchema,
    SiteSchema,
)
from server.types import Classification, Frequency, Series, Source


class AbstractSensorRepository(abc.ABC):
    @abc.abstractclassmethod
    def write_data(self, data: list[SensorDataCreateSchema]) -> None:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_data(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        frequency: Frequency,
        codes: list[str],
        types: list[Classification],
    ) -> list[SensorDataSchema]:
        raise NotImplementedError

    @abc.abstractclassmethod
    def delete_data(self, series: Series, site_id: int) -> None:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_site_average(
        self, series: Series, start: datetime.datetime, end: datetime.datetime
    ) -> list[SiteAverageSchema]:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_latest_date(self, site_id: int, series: Series) -> datetime.datetime:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_sites(self, source: Source | None) -> list[SiteSchema]:
        raise NotImplementedError

    @abc.abstractclassmethod
    def get_site(self, site_code: str) -> SiteSchema:
        raise NotImplementedError
