import datetime
import logging
from fastapi import FastAPI, Response, status, Query
from typing import Annotated
from breathe_london import BreatheLondon
from pydantic import BaseModel

from influx_datastore import InfluxDatastore
import app_config

# Configure logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("httpx")
logger.setLevel(logging.WARNING)

datastore = InfluxDatastore(
    app_config.influx_host,
    app_config.influx_token,
    app_config.influx_org,
    app_config.influx_database,
)

app = FastAPI()


class SensorData(BaseModel):
    # TODO: standardise dt return type. With Z?
    time: datetime.datetime
    value: float


@app.get("/sensor/{site_code}/{series}/{start}/{end}")
def get_sensor_data(
    site_code: str,
    series: str,
    start: str,
    end: str,
    response: Response,
) -> list[SensorData]:
    """Returns sensor data for the specified node, series and time window"""
    if series != "NO2" and series != "PM25":
        response = status.HTTP_400_BAD_REQUEST
        return {"error": f"Invalid series {series}"}

    data = datastore.read_data(
        site_code,
        series,
        datetime.datetime.fromisoformat(start),
        datetime.datetime.fromisoformat(end),
    )

    return data


@app.get("/sensor_average/{series}/{start}/{end}")
def get_sensor_data_average(
    series: str,
    start: str,
    end: str,
    response: Response,
    site: Annotated[list[str] | None, Query()] = None,
) -> list[SensorData]:
    """Returns sensor data, averaged across either all sites (if no
    `site` query parameters are specified), or just the specified
    sites"""
    if series != "NO2" and series != "PM25":
        response = status.HTTP_400_BAD_REQUEST
        return {"error": f"Invalid series {series}"}

    data = datastore.read_average_data(
        series,
        datetime.datetime.fromisoformat(start),
        datetime.datetime.fromisoformat(end),
        site,
    )

    return data


@app.get("/sites")
def get_sites():
    """Returns the list of all sites from the Breathe London API. Note
    that the site list is cached for 24h"""
    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    return breathe_london.get_sites()


@app.get("/healthcheck")
def healthcheck():
    """Healthcheck endpoint when running under fly.dev"""
    return {"status": "ok"}
