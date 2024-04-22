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
    @classmethod
    @abc.abstractmethod
    def write_data(self, data: list[SensorDataCreateSchema]) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_data(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        frequency: Frequency,
        codes: list[str] | None = None,
        types: list[Classification] | None = None,
    ) -> list[SensorDataSchema]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete_data(self, series: Series, site_id: int) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_site_average(
        self, series: Series, start: datetime.datetime, end: datetime.datetime
    ) -> list[SiteAverageSchema]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_latest_date(self, site_id: int, series: Series) -> datetime.datetime:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_sites(self, source: Source | None) -> list[SiteSchema]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_site(self, site_code: str) -> SiteSchema:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_outliers_threshold(
        self, series: Series
    ) -> dict[str, list[SensorDataSchema]]:
        raise NotImplementedError
