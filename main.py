import asyncio
import datetime
import logging
import os
from http import HTTPStatus
from typing import Annotated

import redis.asyncio as redis
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    Security,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis.asyncio.connection import ConnectionPool
from starlette.exceptions import HTTPException

import app_config
from exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)
from middleware import log_request_middleware
from server.logging import configure_logging
from server.schemas import (
    OutlierBlockSchema,
    SensorDataSchema,
    SiteAverageSchema,
    SyncSiteSchema,
)
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

api_key_header = APIKeyHeader(name="X-API-Key")

origins = [
    "https://airaware.static.observableusercontent.com",
    "https://observablehq.com",
    "http://localhost",
    "http://localhost:8080",
    "https://localhost",
    "https://localhost:8080",
    "http://localhost:3000",
    "https://airaware-ui.fly.dev",
    "https://air-aware.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.middleware("http")(log_request_middleware)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in app_config.api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


def request_key_builder(
    func,
    namespace: str = "",
    request: Request = None,
    response: Response = None,
    *args,
    **kwargs,
):
    return ":".join(
        [
            namespace,
            request.method.lower(),
            request.url.path,
            repr(sorted(request.query_params.items())),
        ]
    )


# Initialise redis
@app.on_event("startup")
async def startup():
    pool = ConnectionPool.from_url(url=app_config.redis_url)
    r = redis.Redis(connection_pool=pool)
    enable_cache = bool(int(os.environ.get("ENABLE_CACHE", "1")))
    FastAPICache.init(RedisBackend(r), prefix="fastapi-cache", enable=enable_cache)


# Dependency
def get_unit_of_work() -> AbstractUnitOfWork:
    return UnitOfWork()


def log_request_info(
    request: Request, uow: AbstractUnitOfWork = Depends(get_unit_of_work)
):
    """Logs each request to the database"""
    RequestService.log_request(uow, str(request.url), request.client.host)


@api_router.get("/sensor/{series}/{start}/{end}/{frequency}")
@cache(namespace="api", expire=60 * 60 * 24, key_builder=request_key_builder)  # 1 day
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
@cache(namespace="api", expire=60 * 60 * 24, key_builder=request_key_builder)  # 1 day
def get_site_average_route(
    series: Series,
    start: datetime.datetime,
    end: datetime.datetime,
    enrich: bool = False,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
) -> list[SiteAverageSchema]:
    """Returns the list of all sites with the average levels for the periods given"""
    match SensorService.get_site_average(uow, series, start, end, enrich):
        case ProcessingResult.SUCCESS_RETRIEVED, items:
            return items


@api_router.get("/sites")
# Cache for 6h. A bit shorter than 1 day as this URL doesn't have a date in it and handy to make
# sure it is refreshed a bit more often
@cache(namespace="api", expire=60 * 60 * 6, key_builder=request_key_builder)
def get_sites_route(uow: AbstractUnitOfWork = Depends(get_unit_of_work)):
    """Returns the list of all sites from known data sources"""
    match SensorService.get_sites(uow, None):
        case ProcessingResult.SUCCESS_RETRIEVED, sites:
            return sites


@api_router.get("/geometry/{name}")
# Don't try and cache geometry - borough is quite large and is bigger than the
# max size for upstash redis
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


@api_router.get("/outlier/{series}", status_code=status.HTTP_200_OK)
def get_outliers(
    series: Series,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
) -> dict[str, list[OutlierBlockSchema]]:
    """Returns data that might be questionable. Ie, above a threshold for the specified series"""
    match SensorService.get_outliers_in_context(uow, series):
        case ProcessingResult.SUCCESS_RETRIEVED, data:
            return data


# TODO: add API for updating data
@api_router.post("/resync_data", status_code=status.HTTP_200_OK)
def resync_data(
    data: SyncSiteSchema,
    api_key: str = Security(get_api_key),
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
) -> dict | None:
    """Resyncs the specified sites and clears the site average cache"""
    match SensorService.resync_data(uow, data):
        case ProcessingResult.SUCCESS_UPDATED, _:
            sync_clear_cache()
            return None

        case ProcessingResult.ERROR_NOT_FOUND, detail:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=detail,
            )

        case ProcessingResult.ERROR_INTERNAL_SERVER_ERROR, detail:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=detail,
            )

        case _:
            logging.info("help")


@api_router.get("/healthcheck")
def healthcheck():
    """Healthcheck endpoint when running under fly.dev"""
    return {"status": "ok"}


@api_router.post("/clear_cache", status_code=status.HTTP_200_OK)
async def post_clear_cache(
    api_key: str = Security(get_api_key),
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
) -> dict | None:
    await async_clear_cache()


async def async_clear_cache():
    logging.info("Clearing cache")
    pool = ConnectionPool.from_url(url=app_config.redis_url)
    r = redis.Redis(connection_pool=pool)
    await r.flushdb()
    logging.info("Cache cleared")


def sync_clear_cache():
    try:
        asyncio.get_running_loop().run_until_complete(async_clear_cache())
    except RuntimeError:
        asyncio.run(async_clear_cache())


app.include_router(api_router, dependencies=[Depends(log_request_info)])
