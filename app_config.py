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
database_host = os.environ["DATABASE_HOST"]
redis_url = f"redis://{os.environ['REDIS_HOST']}:6379"

daily_limits = {"pm25": {"who": 15}, "no2": {"who": 25}}
bad_data_limits = {"pm25": 200, "no2": 200}
api_keys = os.environ["API_KEYS"].split(",")
