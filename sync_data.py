import logging
import click

import app_config
from influx_datastore import InfluxDatastore
from site_synchroniser import SiteSynchroniser
from breathe_london import BreatheLondon

# Configure logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("httpx")
logger.setLevel(logging.WARNING)


# site_code = "CLDP0452"
# series = "PM25"
# start = datetime.datetime(2023, 8, 20, 0, 0, 0)
# end = datetime.datetime(2024, 1, 1, 0, 0, 0)

@click.group()
def cli():
    pass

@cli.command()
@click.option('--resync', required=False, default=False, is_flag=True)
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
@click.argument('site_code', required=True)
@click.argument('series', required=True)
@click.option('--resync', required=False, default=False, is_flag=True)
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

if __name__ == '__main__':
    cli()