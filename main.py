from fastapi import FastAPI

from influxdb_client_3 import InfluxDBClient3
import app_config

client = InfluxDBClient3(host=app_config.host, token=app_config.token, org=app_config.org)

app = FastAPI()

@app.get("/")
def read_root():
    query = """SELECT *
    FROM 'census'
    WHERE time >= now() - interval '24 hours'
    AND ('bees' IS NOT NULL OR 'ants' IS NOT NULL)"""

    # Execute the query
    table = client.query(query=query, database="test", language='sql')

    # Convert to dataframe
    df = table.to_pandas().sort_values(by="time")
    print(df)

    return {"Hello": "World"}

@app.get("/healthcheck")
def healthcheck():
     return {"status": "ok"}

