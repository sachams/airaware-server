import logging
import click
import datetime

import app_config
from influx_datastore import InfluxDatastore
from site_synchroniser import SiteSynchroniser
from breathe_london import BreatheLondon
from enricher import Enricher

# Configure logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("httpx")
logger.setLevel(logging.WARNING)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--resync", required=False, default=False, is_flag=True)
@click.option("--pause", required=False, default=0)
@click.option("--start", required=False)
def sync_all(resync, pause, start):
    """Synchronises data between Breathe London and our datastore"""
    datastore = InfluxDatastore(
        app_config.influx_host,
        app_config.influx_token,
        app_config.influx_org,
        app_config.influx_database,
    )

    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    synchroniser = SiteSynchroniser(datastore, breathe_london)

    synchroniser.sync_all(resync, pause, start)


@cli.command()
def sites():
    """Reads site data from Breathe London"""
    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    sites = breathe_london.get_sites()

    for site in sites:
        print(str(site))


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

    datastore = InfluxDatastore(
        app_config.influx_host,
        app_config.influx_token,
        app_config.influx_org,
        app_config.influx_database,
    )

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

    datastore = InfluxDatastore(
        app_config.influx_host,
        app_config.influx_token,
        app_config.influx_org,
        app_config.influx_database,
    )

    start_date = datetime.datetime.fromisoformat(start)
    end_date = datetime.datetime.fromisoformat(end)

    data = datastore.read_site_average(series, start_date, end_date)

    breathe_london = BreatheLondon(app_config.breathe_london_api_key)
    site_metadata = breathe_london.get_sites()
    enriched_data = Enricher.enrich(site_metadata, data)

    for row in enriched_data:
        print(str(row))


if __name__ == "__main__":
    cli()
