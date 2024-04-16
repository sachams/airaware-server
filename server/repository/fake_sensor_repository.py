import datetime

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
from server.types import Classification, Frequency, Series, SiteStatus, Source


class FakeSensorRepository(AbstractSensorRepository):
    def __init__(self):
        self.data = [
            SensorDataSchema(time=datetime.datetime(2020, 6, 5, 3, 2, 1), value=1.23),
            SensorDataSchema(time=datetime.datetime(2020, 6, 5, 3, 2, 1), value=1.23),
        ]

    def write_data(self, data: list[SensorDataCreateSchema]) -> None:
        self.data = data

    def get_data(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
        frequency: Frequency,
        codes: list[str] | None = None,
        types: list[Classification] | None = None,
    ) -> list[SensorDataSchema]:
        return self.data

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
                is_enabled=True,
            ),
            SiteSchema(
                site_id=2,
                site_code="CLDP0002",
                name="Brixton",
                status=SiteStatus.healthy,
                latitude=50.0,
                longitude=-0.01,
                site_type=Classification.roadside,
                source=Source.breathe_london,
                photo_url="https://api.breathelondon.org/assets/images/CLDP0002.jpg",
                description="Brixton Central",
                start_date=datetime.datetime(2022, 6, 5, 3, 2, 1),
                end_date=None,
                borough="Lambeth",
                is_enabled=True,
            ),
            SiteSchema(
                site_id=3,
                site_code="CLDP0003",
                name="Stockwell",
                status=SiteStatus.coming_online,
                latitude=50.1,
                longitude=-0.02,
                site_type=Classification.roadside,
                source=Source.breathe_london,
                photo_url="https://api.breathelondon.org/assets/images/CLDP0003.jpg",
                description="Stockwell primary",
                start_date=datetime.datetime(2022, 6, 5, 3, 2, 1),
                end_date=None,
                borough="Lambeth",
                is_enabled=False,
            ),
        ]

    def get_site(self, site_code: str) -> SiteSchema:
        raise NotImplementedError

    def get_heatmap(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> dict[str, HeatmapSchema]:
        """Gets heatmap data for the specified series by hour of day and day of week, for all
        sites.
        """
        return {
            "CLDP0001": [
                HeatmapSchema(hour=0, day=1, value=0.0),
                HeatmapSchema(hour=1, day=1, value=1.0),
                HeatmapSchema(hour=2, day=1, value=2.0),
                HeatmapSchema(hour=3, day=1, value=3.0),
                HeatmapSchema(hour=4, day=1, value=4.0),
                HeatmapSchema(hour=0, day=2, value=0.0),
                HeatmapSchema(hour=1, day=2, value=2.0),
                HeatmapSchema(hour=2, day=2, value=4.0),
                HeatmapSchema(hour=3, day=2, value=6.0),
                HeatmapSchema(hour=4, day=2, value=8.0),
            ],
            "CLDP0002": [
                HeatmapSchema(hour=0, day=1, value=0.0),
                HeatmapSchema(hour=1, day=1, value=1.5),
                HeatmapSchema(hour=2, day=1, value=3.0),
                HeatmapSchema(hour=3, day=1, value=4.5),
                HeatmapSchema(hour=4, day=1, value=6.0),
                HeatmapSchema(hour=0, day=2, value=0.0),
                HeatmapSchema(hour=1, day=2, value=3.0),
                HeatmapSchema(hour=2, day=2, value=6.0),
                HeatmapSchema(hour=3, day=2, value=9.0),
                HeatmapSchema(hour=4, day=2, value=12.0),
            ],
        }

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
        if series == Series.pm25:
            return {
                "CLDP0002": {"breach": 1, "ok": 1, "no_data": 363},
                "CLDP0001": {"ok": 2, "breach": 0, "no_data": 363},
            }
        else:
            return {
                "CLDP0002": {"breach": 0, "ok": 0, "no_data": 365},
                "CLDP0001": {"breach": 0, "ok": 0, "no_data": 365},
            }

    def get_rank(
        self,
        series: Series,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> dict[str, RankSchema]:
        """Gets the average over the period, and the rank of each site (1 = lowest)"""
        return {
            "CLDP0001": RankSchema(rank=1, value=3.0),
            "CLDP0002": RankSchema(rank=2, value=4.5),
        }

    def get_outliers_threshold(
        self, series: Series
    ) -> dict[str, list[SensorDataSchema]]:
        return {
            "CLDP0001": [
                # Block 1
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 1, 0, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 1, 1, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 1, 2, 0, 0)),
                # Block 2
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 3, 0, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 3, 1, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 3, 2, 0, 0)),
                # Block 3
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 5, 0, 0, 0)),
                # Block 4
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 7, 0, 0, 0)),
            ],
            "CLDP0002": [
                # Block 1
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 1, 0, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 1, 1, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 1, 2, 0, 0)),
                # Block 2
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 3, 0, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 3, 1, 0, 0)),
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 3, 2, 0, 0)),
                # Block 3
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 5, 0, 0, 0)),
                # Block 4
                SensorDataSchema(value=0, time=datetime.datetime(2022, 1, 7, 0, 0, 0)),
            ],
        }
