import datetime
import random

from server.models import SensorDataModel, SiteModel
from server.repository.sensor_repository import SensorRepository
from server.types import Classification, Series, SiteStatus, Source


def _test_add_data(session):
    site_1 = SiteModel(
        site_code="A123",
        name="Test site 1",
        status=SiteStatus.healthy,
        latitude=50.0,
        longitude=0.01,
        site_type=Classification.urban_background,
        source=Source.breathe_london,
    )

    site_2 = SiteModel(
        site_code="A456",
        name="Test site 2",
        status=SiteStatus.healthy,
        latitude=50.0,
        longitude=0.01,
        site_type=Classification.urban_background,
        source=Source.breathe_london,
    )

    session.add_all([site_1, site_2])
    session.commit()

    # Add random heatmap data
    for day in range(1, 3):
        for hour in range(0, 5):
            data_1 = SensorDataModel(
                site_id=site_1.site_id, series=Series.pm25, value=day * hour, time=datetime.datetime(2023, 1, day, hour, 0,0,0)
            )
            data_2 = SensorDataModel(
                site_id=site_2.site_id, series=Series.pm25, value=day * hour * 1.5, time=datetime.datetime(2023, 1, day, hour, 0,0,0)
            )
            session.add_all([data_1, data_2])

    session.commit()


def test_get_site_average(session):

    repository = SensorRepository(session)
    data = repository.get_site_average(
        Series.pm25, datetime.datetime(2022, 1, 1), datetime.datetime(2023, 1, 1)
    )


def test_get_heatmap(session):
    # Populate the database with some data
    # import pdb; pdb.set_trace()

    # site_1 = SiteModel(
    #     site_code="A123",
    #     name="Test site 1",
    #     status=SiteStatus.healthy,
    #     latitude=50.0,
    #     longitude=0.01,
    #     site_type=Classification.urban_background,
    #     source=Source.breathe_london,
    # )

    # site_2 = SiteModel(
    #     site_code="A456",
    #     name="Test site 2",
    #     status=SiteStatus.healthy,
    #     latitude=50.0,
    #     longitude=0.01,
    #     site_type=Classification.urban_background,
    #     source=Source.breathe_london,
    # )

    # session.add_all([site_1, site_2])
    # session.commit()

    # # Add random heatmap data
    # for day in range(1, 32):
    #     for hour in range(0, 24):
    #         data_1 = SensorDataModel(
    #             site_id=site_1.site_id, series=Series.pm25, value=random.uniform(0, 20), time=datetime.datetime(2023, 1, day, hour, 0,0,0)
    #         )
    #         data_2 = SensorDataModel(
    #             site_id=site_2.site_id, series=Series.pm25, value=random.uniform(0, 20), time=datetime.datetime(2023, 1, day, hour, 0,0,0)
    #         )
    #         session.add_all([data_1, data_2])

    # session.commit()

    repository = SensorRepository(session)
    data = repository.get_heatmap(
        Series.pm25, datetime.datetime(2023, 1, 1), datetime.datetime(2024, 1, 1)
    )


def test_get_breach(session):
    repository = SensorRepository(session)

    data = repository.get_breach(
        Series.no2, datetime.datetime(2023, 1, 1), datetime.datetime(2024, 1, 1), 5
    )

def test_get_rank(session):
    repository = SensorRepository(session)

    data = repository.get_rank(
        Series.pm25, datetime.datetime(2023, 1, 1), datetime.datetime(2024, 1, 1)
    )

