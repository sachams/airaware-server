import datetime
import json

import click
from reproj_geojson import ReprojGeojson

from server.database import SessionLocal
from server.logging import configure_logging
from server.service import SensorService
from server.types import Series, Source
from server.unit_of_work.unit_of_work import UnitOfWork

# Configure logging
configure_logging()


@click.group()
def cli():
    pass


@cli.command()
def sync_sites():
    """Syncs site data from remote sources to the database"""
    uow = UnitOfWork()
    SensorService.sync_sites(uow)


@cli.command()
@click.argument("site_code", required=True)
@click.argument("series", required=True, type=click.Choice(Series))
@click.argument("source", required=True, type=click.Choice(Source))
@click.option("--resync", required=False, default=False, is_flag=True)
def sync(site_code: str, series: Series, source: Source, resync: bool):
    """Synchronises a single site between remote sources and our datastore"""
    uow = UnitOfWork()
    SensorService.sync_single_site_data(uow, site_code, None, source, series, resync)


@cli.command()
@click.option("--resync", required=False, default=False, is_flag=True)
@click.option("--start", required=False)
def sync_all(resync, start):
    """Synchronises all data between remote sources and our datastore"""
    uow = UnitOfWork()
    SensorService.sync_all(uow, resync, start)


@cli.command()
@click.argument("site_code", required=True)
@click.argument("series", required=True)
def last_time(site_code, series):
    """Returns the last date/time for the site and series"""
    import pdb

    pdb.set_trace()

    datastore = PostgresDatastore(SessionLocal())
    print(datastore.get_latest_date(site_code, series))


@cli.command()
@click.argument("series", required=True)
@click.argument("start", required=True)
@click.argument("end", required=True)
@click.option(
    "--frequency",
    "-f",
    required=False,
    default="hourly",
    type=click.Choice(["hourly", "daily"]),
)
@click.option("--site_code", "-s", multiple=True, required=False)
def datastore_read(series, start, end, site_code, frequency):
    """Reads data from the datastore, averaging across all nodes, or optionally just
    the specified node(s)"""

    datastore = PostgresDatastore(SessionLocal())

    start_date = datetime.datetime.fromisoformat(start)
    end_date = datetime.datetime.fromisoformat(end)

    data = datastore.read_data(series, start_date, end_date, site_code, frequency)

    for row in data:
        print(str(row))


@cli.command()
@click.argument("series", required=True)
@click.argument("start", required=True)
@click.argument("end", required=True)
def datastore_read_site_average(series, start, end):
    """Reads data from the datastore, averaging across all nodes, or optionally just
    the specified node(s)"""

    datastore = PostgresDatastore(SessionLocal())

    start_date = datetime.datetime.fromisoformat(start)
    end_date = datetime.datetime.fromisoformat(end)

    data = datastore.read_site_average(series, start_date, end_date)

    for row in data:
        print(str(row))


@cli.command()
@click.argument("src_filename", required=True, type=click.Path(exists=True))
@click.argument("dest_filename", required=True, type=click.Path())
@click.argument("src_proj", default="EPSG:27700")
@click.argument("dest_proj", default="WGS84")
def reproject_geojson(src_filename, dest_filename, src_proj, dest_proj):
    """Converts geojson from one coordinate system to another"""

    with open(src_filename, "r") as src_file, open(dest_filename, "w") as dest_file:
        src_geojson = json.load(src_file)
        dest_geojson = ReprojGeojson.transform(src_geojson, src_proj, dest_proj)
        json.dump(dest_geojson, dest_file, indent=2)


if __name__ == "__main__":
    cli()
