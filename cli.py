import json

import click
from reproj_geojson import ReprojGeojson

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
