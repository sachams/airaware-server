import logging
import click
import datetime

import app_config
from influx_datastore import InfluxDatastore
from site_synchroniser import SiteSynchroniser
from breathe_london import BreatheLondon

# Configure logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("httpx")
logger.setLevel(logging.WARNING)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--resync", required=False, default=False, is_flag=True)
def sync_all(resync):
    """Synchronises data between Breathe London and our datastore"""
    datastore = InfluxDatastore(
        app_config.influx_host,
        app_config.influx_token,
        app_config.influx_org,
        app_config.influx_database,
    )

    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    synchroniser = SiteSynchroniser(datastore, breathe_london)

    synchroniser.sync_all(resync)


@cli.command()
@click.argument("site_code", required=True)
@click.argument("series", required=True)
@click.option("--resync", required=False, default=False, is_flag=True)
def sync(site_code, series, resync):
    """Synchronises data between Breathe London and our datastore"""
    datastore = InfluxDatastore(
        app_config.influx_host,
        app_config.influx_token,
        app_config.influx_org,
        app_config.influx_database,
    )

    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    synchroniser = SiteSynchroniser(datastore, breathe_london)
    synchroniser.sync(site_code, series, resync)


@cli.command()
@click.argument("site_code", required=True)
@click.argument("series", required=True)
@click.argument("start", required=True)
@click.argument("end", required=True)
def datastore_read(site_code, series, start, end):
    """Reads data from the datastore"""
    datastore = InfluxDatastore(
        app_config.influx_host,
        app_config.influx_token,
        app_config.influx_org,
        app_config.influx_database,
    )

    start_date = datetime.datetime.fromisoformat(start)
    end_date = datetime.datetime.fromisoformat(end)

    data = datastore.read_data(site_code, series, start_date, end_date)

    for row in data:
        print(str(row))


@cli.command()
@click.argument("series", required=True)
@click.argument("start", required=True)
@click.argument("end", required=True)
@click.option("--site_code", "-s", multiple=True, required=False)
def datastore_read_avg(series, start, end, site_code):
    """Reads data from the datastore, averaging across all nodes, or optionally just
    the specified nodes"""
    datastore = InfluxDatastore(
        app_config.influx_host,
        app_config.influx_token,
        app_config.influx_org,
        app_config.influx_database,
    )

    start_date = datetime.datetime.fromisoformat(start)
    end_date = datetime.datetime.fromisoformat(end)

    data = datastore.read_average_data(series, start_date, end_date, site_code)

    for row in data:
        print(str(row))


if __name__ == "__main__":
    cli()
