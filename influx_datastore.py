import logging
import pyarrow as pa

from influxdb_client_3 import (
    InfluxDBClient3,
    write_client_options,
    WriteOptions,
    InfluxDBError,
    Point,
)


class InfluxDatastore:
    def __init__(self, host, token, org, database):
        # Instantiate WriteOptions for batching
        # write_options = WriteOptions()
        # wco = write_client_options(success_callback=self.success,
        #                             error_callback=self.error,
        #                             retry_callback=self.retry,
        #                             WriteOptions=write_options)
        logging.info(f"Connecting to {database} on {host} at {org}")
        self.client = InfluxDBClient3(
            host=host, token=token, org=org, database=database
        )

    # def success(self, conf, data: str):
    #     print(f"Written batch: {conf}, data: {data}")

    # def error(self, conf, data: str, exception: InfluxDBError):
    #     print(f"Cannot write batch: {conf}, data: {data} due: {exception}")

    # def retry(self, conf, data: str, exception: InfluxDBError):
    #     print(f"Retryable error occurs for batch: {conf}, data: {data} retry: {exception}")

    @staticmethod
    def _parse_row(series, row):
        """Extracts a single row of sensor data that is expected to be a dict in the format:
        {'SiteCode': 'CLDP0452',
        'DateTime': '2023-06-12T10:00:00.000Z',
        'DurationNS': 3600000000,
        'ScaledValue': 12.983285921708745}
        """
        if row["ScaledValue"] is None:
            raise Exception(f"ScaledValue is None. Record is {row}")
        
        if row["DateTime"] is None:
            raise Exception(f"DateTime is None. Record is {row}")

        return (
            Point("sensor_data")
            .tag("site_code", row["SiteCode"])
            .field(series, float(row["ScaledValue"]))
            .time(row["DateTime"])
        )

    @staticmethod
    def _parse(series, data):
        """Converts the JSON input data into an array of InfluxDB Points"""
        points = [InfluxDatastore._parse_row(series, row) for row in data]
        return points

    def write_data(self, series, data):
        """Writes Breathe London series data to the database"""
        points = InfluxDatastore._parse(series, data)

        self.client.write(record=points)

        # for point in points:
        #     print(f"Writing: {str(point)}")
        #     self.client.write(record=[point])

    def get_latest_date(self, site_code, series):
        """Queries Influx to get the latest date of the given series"""
        query = (
            f"select selector_last('{series}', time)['time']"
            "from sensor_data "
            f"where site_code = '{site_code}'"
        )

        try:
            last_date = self.client.query(query=query, language="sql")[0][0].as_py()
        except pa.lib.ArrowInvalid as e:
            # This indicates the table can't be found
            return None

        if last_date is None:
            return None

        return last_date.to_pydatetime()
