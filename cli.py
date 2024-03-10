import json

import click

from reproj_geojson import ReprojGeojson
from server.logging import configure_logging
from server.service import ProcessingResult, SensorService
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
@click.argument("series", required=True, type=click.Choice(Series))
@click.option("--filename", required=False, default="bad_data.csv")
def bad_data(series, filename):
    """Synchronises all data between remote sources and our datastore"""
    uow = UnitOfWork()
    result, bad_data = SensorService.get_bad_data(uow, series)

    # Display a summary of the bad data
    # for site_code, data in bad_data.items():
    #     print(f"Site code: {site_code} - {len(data)} bad data points")
    # for row in data:
    #     print(row)

    # And dump it out to a CSV file
    print(f"Writing to {series}_{filename}")
    with open(f"{series}_{filename}", "w") as dest_file:
        for site_code, data in bad_data.items():
            for row in data:
                dest_file.write(
                    f"{site_code},{series.name},{row.time.strftime('%d/%m/%Y %H:%M')},{row.value}\n"
                )


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


@cli.command()
@click.argument("year", required=True, type=int)
def wrapped(year):
    """Generates Wrapped summary statistics for the specified year"""
    import json

    from pydantic.json import pydantic_encoder

    uow = UnitOfWork()

    match SensorService.generate_wrapped(uow, year):
        case ProcessingResult.SUCCESS_RETRIEVED, data:
            with open(f"wrapped_{year}.json", "w") as file:
                json_data = json.dumps(data, default=pydantic_encoder)
                file.write(json_data)


if __name__ == "__main__":
    cli()
