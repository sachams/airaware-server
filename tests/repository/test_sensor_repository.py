from datetime import datetime

import pytest

from server.models import SensorDataModel, SiteModel
from server.repository.sensor_repository import SensorRepository
from server.schemas import SensorDataCreateSchema
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
                site_id=site_1.site_id,
                series=Series.pm25,
                value=day * hour,
                time=datetime(2023, 1, day, hour, 0, 0, 0),
            )
            data_2 = SensorDataModel(
                site_id=site_2.site_id,
                series=Series.pm25,
                value=day * hour * 1.5,
                time=datetime(2023, 1, day, hour, 0, 0, 0),
            )
            session.add_all([data_1, data_2])

    session.commit()


def test_get_site_average(session):

    repository = SensorRepository(session)
    data = repository.get_site_average(
        Series.pm25, datetime(2022, 1, 1), datetime(2023, 1, 1)
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
        Series.pm25, datetime(2023, 1, 1), datetime(2024, 1, 1)
    )


def test_get_breach(session):
    repository = SensorRepository(session)

    data = repository.get_breach(
        Series.no2, datetime(2023, 1, 1), datetime(2024, 1, 1), 5
    )


def test_get_rank(session):
    repository = SensorRepository(session)

    data = repository.get_rank(Series.pm25, datetime(2023, 1, 1), datetime(2024, 1, 1))


def test_get_outliers(session, dummy_sites):
    repository = SensorRepository(session)
    # Add some data
    repository.update_sites(dummy_sites)
    session.commit()

    # We need to read the sites back after saving them to get the site_id
    sites = repository.get_sites(None)

    # Add some data - good and bad
    data = [
        SensorDataCreateSchema(
            site_id=sites[0].site_id,
            series=Series.pm25,
            value=1,
            time=datetime(2023, 1, 1, 0, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[0].site_id,
            series=Series.no2,
            value=2,
            time=datetime(2023, 1, 1, 1, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[0].site_id,
            series=Series.pm25,
            value=200,
            time=datetime(2023, 1, 1, 2, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[0].site_id,
            series=Series.pm25,
            value=201,
            time=datetime(2023, 1, 1, 3, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[0].site_id,
            series=Series.no2,
            value=202,
            time=datetime(2023, 1, 1, 4, 0, 0, 0),
        ),
        # Site 1
        SensorDataCreateSchema(
            site_id=sites[1].site_id,
            series=Series.pm25,
            value=11,
            time=datetime(2023, 1, 1, 0, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[1].site_id,
            series=Series.no2,
            value=12,
            time=datetime(2023, 1, 1, 1, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[1].site_id,
            series=Series.pm25,
            value=300,
            time=datetime(2023, 1, 1, 2, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[1].site_id,
            series=Series.pm25,
            value=301,
            time=datetime(2023, 1, 1, 3, 0, 0, 0),
        ),
        SensorDataCreateSchema(
            site_id=sites[1].site_id,
            series=Series.no2,
            value=302,
            time=datetime(2023, 1, 1, 4, 0, 0, 0),
        ),
    ]

    repository.write_data(data)
    session.commit()

    # Now query for bad data
    outliers = repository.get_outliers_threshold(Series.pm25)

    assert len(outliers.keys()) == 2
    assert sites[0].site_code in outliers.keys()
    assert sites[1].site_code in outliers.keys()

    assert len(outliers[sites[0].site_code]) == 1
    assert outliers[sites[0].site_code][0].value == pytest.approx(201)

    assert len(outliers[sites[1].site_code]) == 2
    assert outliers[sites[1].site_code][0].value == pytest.approx(300)
    assert outliers[sites[1].site_code][1].value == pytest.approx(301)
