import datetime
import logging
from fastapi import FastAPI, Response, status, Query
from typing import Annotated, Tuple
from breathe_london import BreatheLondon
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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

origins = [
    "https://airaware.static.observableusercontent.com",
    "https://observablehq.com",
    "http://localhost",
    "http://localhost:8080",
    "https://localhost",
    "https://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitise_timestamp(dt):
    """Sanitises datetime inputs"""

    # If the format includes milliseconds, strip them
    # eg, 2023-08-23T00:00:00.000Z
    return dt.split(".")[0]


@app.get("/sensor/{series}/{start}/{end}/{frequency}")
def get_sensor_data(
    series: str,
    start: str,
    end: str,
    frequency: str,
    response: Response,
    site: Annotated[list[str] | None, Query()] = None,
) -> list[Tuple[int, float]]:
    """Returns sensor data, averaged across either all sites (if no
    `site` query parameters are specified), or just the specified
    sites"""
    series = series.upper()
    if series != "NO2" and series != "PM25":
        response = status.HTTP_400_BAD_REQUEST
        return {"error": f"Invalid series {series}"}

    frequency = frequency.lower()
    if frequency != "hourly" and frequency != "daily":
        response = status.HTTP_400_BAD_REQUEST
        return {"error": f"Invalid frequency {frequency}"}

    data = datastore.read_data(
        series,
        datetime.datetime.fromisoformat(sanitise_timestamp(start)),
        datetime.datetime.fromisoformat(sanitise_timestamp(end)),
        site,
        frequency,
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
