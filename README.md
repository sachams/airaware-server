# AirAware server

The AirAware server is a FastAPI-based web server that stores air quality data in a Postgres/TimescaleDB database.

## Development notes

### Export to requirements.txt

```sh
poetry export --without dev --without-hashes -f requirements.txt --output requirements.txt
```

```sh
poetry export --only dev --without-hashes -f requirements.txt --output dev_requirements.txt
```

### Start a fly database proxy

```sh
fly proxy 5432 -a breathe-air-postgres
```

### Generate a migration

```sh
alembic revision --autogenerate -m "name_of_the_migration"
```

### Create a postgres app

```sh
fly postgres create --image-ref flyio/postgres:14.4
```

### Install timescaledb

1. Install library:

    ```sh
    fly pg config update --shared-preload-libraries timescaledb --app breathe-air-postgres
    ```

1. Enable extension. Connect to psql and run:

```sh
```

## Useful queries

### Annual averages (eg, NO2)

```sql
with main as (SELECT site.site_code, avg(sensor_data.value) AS mean
FROM sensor_data 
JOIN site ON site.site_id = sensor_data.site_id
WHERE sensor_data.series = 'no2'
AND sensor_data.time >= '2023-01-01 00:00:00'
AND sensor_data.time < '2024-01-01 00:00:00'
GROUP BY site.site_code 
ORDER BY site.site_code)

select main.site_code, site.name, site.latitude, site.longitude, site.borough, main.mean
from main 
join site on main.site_code = site.site_code
where site.is_enabled='TRUE';
```