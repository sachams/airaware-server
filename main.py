import json
import os
import datetime
import logging
from fastapi import Depends, FastAPI, Response, status, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated, Tuple
from breathe_london import BreatheLondon
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from server.postgres_datastore import PostgresDatastore
import app_config
from server.database import SessionLocal, engine
from sqlalchemy.orm import Session
from server.schemas import SensorData, SiteAverage

# Configure logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("httpx")
logger.setLevel(logging.WARNING)

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


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    db: Session = Depends(get_db),
) -> list[SensorData] | dict:
    """Returns sensor data, averaged across either all sites (if no
    `site` query parameters are specified), or just the specified
    sites"""
    series = series.upper()
    if series != "NO2" and series != "PM25":
        raise HTTPException(status_code=400, detail=f"Invalid series {series}")

    frequency = frequency.lower()
    if frequency != "hourly" and frequency != "daily":
        raise HTTPException(status_code=400, detail=f"Invalid frequency {frequency}")

    datastore = PostgresDatastore(db)

    data = datastore.read_data(
        series,
        datetime.datetime.fromisoformat(sanitise_timestamp(start)),
        datetime.datetime.fromisoformat(sanitise_timestamp(end)),
        site,
        frequency,
    )

    return data


@app.get("/site_average/{series}/{start}/{end}")
def get_site_average(
    series: str,
    start: str,
    end: str,
    db: Session = Depends(get_db),
) -> list[SiteAverage] | dict:
    """Returns the list of all sites with the average levels for the periods given"""
    series = series.upper()
    if series != "NO2" and series != "PM25":
        raise HTTPException(status_code=400, detail=f"Invalid series {series}")

    datastore = PostgresDatastore(db)

    data = datastore.read_site_average(
        series,
        datetime.datetime.fromisoformat(sanitise_timestamp(start)),
        datetime.datetime.fromisoformat(sanitise_timestamp(end)),
    )

    return data


@app.get("/site_info")
def get_site_info():
    """Returns the list of all sites from the Breathe London API. Note
    that the site list is cached for 24h"""
    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    return breathe_london.get_sites()


@app.get("/geometry/{name}")
def get_geometry(name: str) -> str | dict:
    """Returns the named geometry. The name will have a .json extension added
    and will be searched for in the geometry folder"""
    path = f"geometry/{name}.json"

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Invalid geometry {name}")

    with open(path, "r") as geometry_file:
        geometry = json.load(geometry_file)
        return geometry


@app.get("/healthcheck")
def healthcheck():
    """Healthcheck endpoint when running under fly.dev"""
    return {"status": "ok"}
