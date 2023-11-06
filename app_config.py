import os

from dotenv import load_dotenv

load_dotenv()

influx_token = os.environ["INFLUX_API_TOKEN"]
influx_database = "data"
influx_org = "Breathe London"
influx_host = "https://eu-central-1-1.aws.cloud2.influxdata.com"

breathe_london_api_key = os.environ["BREATHE_LONDON_API_KEY"]
database_username = os.environ["DATABASE_USERNAME"]
database_password = os.environ["DATABASE_PASSWORD"]
database_name = os.environ["DATABASE_NAME"]
