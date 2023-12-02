import datetime

from server.repository.abstract_sensor_repository import AbstractSensorRepository
from server.schemas import (
    SensorDataCreateSchema,
    SensorDataSchema,
    SiteAverageSchema,
    SiteSchema,
)
from server.types import Classification, Frequency, Series, SiteStatus, Source


class FakeSensorRepository(AbstractSensorRepository):
    def __init__(self):
        self.data = []

    def write_data(self, data: list[SensorDataCreateSchema]) -> None:
        self.data = data

    def get_data(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        frequency: Frequency,
        codes: list[str],
        types: list[Classification],
    ) -> list[SensorDataSchema]:
        return [
            SensorDataSchema(time=datetime.datetime(2020, 6, 5, 3, 2, 1), value=1.23),
            SensorDataSchema(time=datetime.datetime(2020, 6, 5, 3, 2, 1), value=1.23),
        ]

    def delete_data(self, series: Series, site_id: int) -> None:
        raise NotImplementedError

    def get_site_average(
        self, series: Series, start: datetime.datetime, end: datetime.datetime
    ) -> list[SiteAverageSchema]:
        return [
            SiteAverageSchema(site_code="CLDP0001", value=1.23),
            SiteAverageSchema(site_code="CLDP0002", value=4.56),
        ]

    def get_latest_date(self, site_id: int, series: Series) -> datetime.datetime:
        return datetime.datetime(2020, 6, 5, 3, 2, 1)

    def get_sites(self, source: Source | None) -> list[SiteSchema]:
        return [
            SiteSchema(
                site_id=1,
                site_code="CLDP0001",
                name="Royal London University Hospital",
                status=SiteStatus.healthy,
                latitude=51.518775939941406,
                longitude=-0.059463899582624435,
                site_type=Classification.urban_background,
                source=Source.breathe_london,
                photo_url="https://api.breathelondon.org/assets/images/CLDP0001.jpg",
                description="The Royal London Hospital is home to one of the largest...",
                start_date=datetime.datetime(2020, 6, 5, 3, 2, 1),
                end_date=datetime.datetime(2022, 6, 5, 3, 2, 1),
                borough="Lambeth",
            ),
            SiteSchema(
                site_id=2,
                site_code="CLDP0002",
                name="Brixton",
                status=SiteStatus.coming_online,
                latitude=50.0,
                longitude=-0.01,
                site_type=Classification.roadside,
                source=Source.breathe_london,
                photo_url="https://api.breathelondon.org/assets/images/CLDP0002.jpg",
                description="Brixton Central",
                start_date=datetime.datetime(2022, 6, 5, 3, 2, 1),
                end_date=None,
                borough="Lambeth",
            ),
        ]

    def get_site(self, site_code: str) -> SiteSchema:
        raise NotImplementedError
