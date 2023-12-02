import datetime
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from server.logging import configure_logging
from server.schemas import SensorDataSchema, SiteAverageSchema
from server.service import (
    GeometryService,
    ProcessingResult,
    RequestService,
    SensorService,
)
from server.types import Classification, Frequency, Series
from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork
from server.unit_of_work.unit_of_work import UnitOfWork

# Configure logging
configure_logging()

app = FastAPI()
api_router = APIRouter()

origins = [
    "https://airaware.static.observableusercontent.com",
    "https://observablehq.com",
    "http://localhost",
    "http://localhost:8080",
    "https://localhost",
    "https://localhost:8080",
    "http://localhost:3000",
    "https://airaware-ui.fly.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_unit_of_work() -> AbstractUnitOfWork:
    return UnitOfWork()


def log_request_info(
    request: Request, uow: AbstractUnitOfWork = Depends(get_unit_of_work)
):
    """Logs each request to the database"""
    RequestService.log_request(uow, str(request.url), request.client.host)


@api_router.get("/sensor/{series}/{start}/{end}/{frequency}")
def get_sensor_data_route(
    series: Series,
    start: datetime.datetime,
    end: datetime.datetime,
    frequency: Frequency,
    codes: Annotated[list[str] | None, Query()] = None,
    types: Annotated[list[Classification] | None, Query()] = None,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
) -> list[SensorDataSchema]:
    """Returns sensor data, averaged across either all sites (if no
    `site` query parameters are specified), or just the specified
    sites"""
    match SensorService.get_data(uow, series, start, end, frequency, codes, types):
        case ProcessingResult.SUCCESS_RETRIEVED, items:
            return items


@api_router.get("/site_average/{series}/{start}/{end}")
def get_site_average_route(
    series: Series,
    start: datetime.datetime,
    end: datetime.datetime,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
) -> list[SiteAverageSchema]:
    """Returns the list of all sites with the average levels for the periods given"""
    match SensorService.get_site_average(uow, series, start, end):
        case ProcessingResult.SUCCESS_RETRIEVED, items:
            return items


@api_router.get("/sites")
def get_sites_route(uow: AbstractUnitOfWork = Depends(get_unit_of_work)):
    """Returns the list of all sites from known data sources"""
    match SensorService.get_sites(uow, None):
        case ProcessingResult.SUCCESS_RETRIEVED, sites:
            return sites


@api_router.get("/geometry/{name}")
def get_geometry_route(
    name: str, uow: AbstractUnitOfWork = Depends(get_unit_of_work)
) -> dict:
    """Returns the named geometry. The name will have a .json extension added
    and will be searched for in the geometry folder"""
    match GeometryService.get_geometry(uow, name):
        case ProcessingResult.SUCCESS_RETRIEVED, geometry:
            return geometry

        case ProcessingResult.ERROR_NOT_FOUND:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=f"Unknown geometry {name}"
            )


@api_router.get("/healthcheck")
def healthcheck():
    """Healthcheck endpoint when running under fly.dev"""
    return {"status": "ok"}


app.include_router(api_router, dependencies=[Depends(log_request_info)])
