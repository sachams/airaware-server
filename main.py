import datetime
import logging
from fastapi import FastAPI, Response, status
from breathe_london import BreatheLondon

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


@app.get("/sensor/{site_code}/{series}/{start}/{end}")
def get_sensor_data(
    site_code: str,
    series: str,
    start: str,
    end: str,
    response: Response,
):
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


@app.get("/sites")
def get_sites():
    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    return breathe_london.get_sites()


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}
