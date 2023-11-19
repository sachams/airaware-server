import datetime

from server.repository.sensor_repository import SensorRepository
from server.types import Series


def test_get_site_average(session):
    # # Populate the datanase with some data
    # site = SiteModel(
    #     site_code="A123",
    #     name="Test site",
    #     status=SiteStatus.healthy,
    #     latitude=50.0,
    #     longitude=0.01,
    #     site_type=Classification.urban_background,
    #     source=Source.breathe_london,
    # )

    # session.add(site)
    # session.commit()

    # data_1 = SensorDataModel(
    #     site_id=site.site_id, series=Series.pm25, value=1.234, time=datetime.datetime.utcnow()
    # )
    # data_2 = SensorDataModel(
    #     site_id=site.site_id, series=Series.no2, value=4.567, time=datetime.datetime.utcnow()
    # )

    # session.add_all([data_1, data_2])
    # session.commit()

    repository = SensorRepository(session)
    data = repository.get_site_average(
        Series.pm25, datetime.datetime(2022, 1, 1), datetime.datetime(2023, 1, 1)
    )
