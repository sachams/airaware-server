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
        # self.table = "test_table"
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

    def _parse_row(self, series, row):
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
            Point(series)
            .tag("site_code", row["SiteCode"])
            .field("value", float(row["ScaledValue"]))
            .time(row["DateTime"])
        )

    def _parse(self, series, data):
        """Converts the JSON input data into an array of InfluxDB Points"""
        points = [
            self._parse_row(series, row)
            for row in data
            if row["ScaledValue"] is not None
        ]
        return points

    def write_data(self, series, data):
        """Writes Breathe London series data to the database"""
        points = self._parse(series, data)

        self.client.write(record=points)

    @staticmethod
    def _isoformat_utc(dt):
        # The normal datetime.isoformat() doesn't include the timezone (Z = UTC)
        # so add this now
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def read_data(self, site_code, series, start, end):
        """Reads data from the datastore, and returns it in this format:
        [
            {
                'time': '2023-06-12T10:00:00',
                'value': 12.983285921708745
            }
        ]
        """
        query = (
            "select time, value "
            f'from "{series}" '
            f"where site_code = '{site_code}' "
            f"and time >= '{InfluxDatastore._isoformat_utc(start)}' "
            f"and time < '{InfluxDatastore._isoformat_utc(end)}' "
            "order by time asc"
        )

        try:
            results = self.client.query(query=query, language="sql", mode="pandas")
        except pa.lib.ArrowInvalid as e:
            # This indicates the table can't be found
            return []

        return self.format_results(results)

    def read_average_data(self, series, start, end, site_codes):
        """Reads data from the datastore, averaging across the specified sites. If no
        sites are specified, it averages across all sites.
        and returns it in this format:
        [
            {
                'time': '2023-06-12T10:00:00',
                'value': 12.983285921708745
            }
        ]
        """
        site_clause = ""

        if site_codes:
            formatted_site_codes = ",".join(
                [f"'{site_code}'" for site_code in site_codes]
            )
            site_clause = f"and site_code in ({formatted_site_codes})"

        query = (
            "select time, avg(value) as 'value' "
            f'from "{series}" '
            f"where time >= '{InfluxDatastore._isoformat_utc(start)}' "
            f"and time < '{InfluxDatastore._isoformat_utc(end)}' "
            f"{site_clause} "
            "group by time "
            "order by time asc"
        )

        try:
            results = self.client.query(query=query, language="sql", mode="pandas")
        except pa.lib.ArrowInvalid as e:
            # This indicates the table can't be found
            return []

        return self.format_results(results)

    def format_results(self, results):
        data = []

        for _, row in results.iterrows():
            point = {
                "time": row["time"].strftime("%Y-%m-%dT%H:%M:%S"),
                "value": row["value"],
            }
            data.append(point)

        return data

    def get_latest_date(self, site_code, series):
        """Queries Influx to get the latest date of the given series"""
        query = (
            f"select selector_last('value', time)['time']"
            f"from {series} "
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
