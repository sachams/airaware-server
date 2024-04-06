# AirAware server

The AirAware server is a FastAPI-based web server that stores air quality data in a Postgres/TimescaleDB database.

## Development notes

### Export to requirements.txt

```sh
poetry export --without-hashes -f requirements.txt --output requirements.txt
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

## Compressing GeoJSON

Use the [GeoJSON Minify tool](https://open-innovations.github.io/geojson-minify/)

## Converting shapefile to geojson

https://mygeodata.cloud/converter/shp-to-geojson