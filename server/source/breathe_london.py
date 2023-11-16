import datetime
import logging
import time

import httpx
from borough_mapper import BoroughMapper

from server.schemas import SensorDataSchema, SiteSchema
from server.types import Classification, Series, SiteStatus, Source

"""BreatheLondon Site data looks like this:
    {
        "SiteCode": "CLDP0001",
        "SiteName": "Royal London University Hospital",
        "Latitude": 51.518775939941406,
        "Longitude": -0.059463899582624435,
        "LocalAuthorityID": null,
        "SiteClassification": "Urban Background",
        "HeadHeight": 2.4000000953674316,
        "ToRoad": 30,
        "SiteLocationType": "Hospital",
        "Indoor": 0,
        "SitePhotoURL": "https://api.breathelondon.org/assets/images/CLDP0001.jpg",
        "SiteDescription": "The Royal London Hospital is home to one of the largest...",
        "SleepTime": 1200,
        "BatteryStatus": "discharging normally",
        "BatteryPercentage": 91,
        "SignalStrength": "4-excellent",
        "SensorsHealthStatus": "OK",
        "OverallStatus": "Healthy",
        "DeviceCode": "A7Y9WHYD",
        "StartDate": "2021-01-22T08:59:25.167Z",
        "EndDate": null,
        "LastCommunication": "2023-11-10T04:17:32.543Z",
        "InputPowerError": 0,
        "InputPowerCurrent": 0,
        "InputPowerVoltage": 0,
        "InputBatteryError": 0,
        "InputBatteryVoltage": 3.8635923862457275,
        "ChargingStatus": 7,
        "SignalQuality": 31,
        "BatterySleepMultiplier": 4,
        "WeatherError": 0,
        "PMError": 0,
        "NO2Error": 0,
        "LatestINO2Value": null,
        "LatestINO2Index": null,
        "LatestINO2IndexSource": null,
        "LatestIPM10Value": null,
        "LatestIPM10NUMValue": null,
        "LatestIPM1Value": null,
        "LatestIPM1NUMValue": null,
        "LatestIPM25Value": null,
        "LatestIPM25Index": null,
        "LatestIPM25IndexSource": null,
        "LatestIPM25NUMValue": null,
        "LatestRELHUMValue": null,
        "LatestTEMPERATValue": null,
        "SiteActive": 1,
        "SiteGroup": "GLA",
        "PowerTag": "Solar",
        "Enabled": "Y",
        "OtherTags": "Deployed, GLA, Solar300, Tower Hamlets, V1",
        "OrganisationName": "Mayor of London",
        "SponsorName": "Mayor of London",
        "HourlyBulletinEnd": "Nov 10 2023  6:00AM",
        "Borough": "Tower Hamlets"
    },
"""


class BreatheLondon:
    def __init__(self, api_key):
        # Check if a directory called /data exists. If so, use it as the file root
        self.max_retries = 3
        self.retry_pause = 1
        self.client = httpx.Client(timeout=30)
        self.api_key = api_key
        self.base_url = "https://api.breathelondon.org/api"
        self.borough_mapper = BoroughMapper()

    @property
    def name(self):
        return "Breathe London"

    def _get(self, endpoint):
        """Makes a GET request from the endpoint"""
        params = {"key": self.api_key}
        url = f"{self.base_url}/{endpoint}"

        retry_count = 0
        while True:
            try:
                response = self.client.get(url, params=params)
                return response.json()
            except httpx.HTTPError as e:
                if retry_count >= self.max_retries:
                    logging.error(
                        f"Caught exception while requesting data from API: {str(e)}. Retry limit reached"
                    )
                    raise

                retry_count += 1
                logging.warning(f"{str(e)}. Pausing {self.retry_pause}s before retry")
                time.sleep(self.retry_pause)

    def _get_status_enum(self, status):
        # Remove any spaces and convert to lower case before matching.
        # This cleans up some variations
        match status.lower().replace(" ", ""):
            case "healthy":
                return SiteStatus.healthy

            case "offline":
                return SiteStatus.offline

            case "comingonline":
                return SiteStatus.coming_online

            case "needsattention":
                return SiteStatus.needs_attention

            case _:
                return SiteStatus.unknown

    def _get_classification_enum(self, classification):
        # Convert to lower case before matching.
        match classification.lower():
            case "urban background":
                return Classification.urban_background

            case "suburban":
                return Classification.suburban

            case "kerbside":
                return Classification.kerbside

            case "industrial":
                return Classification.industrial

            case "roadside":
                return Classification.roadside

            case "rural":
                return Classification.rural

            case _:
                return Classification.unknown

    def get_sites(self) -> list[SiteSchema]:
        """Requests a list of sites from Breathe London and returns list of sites"""

        logging.info("Loading site list from API")
        site_list = self._get("ListSensors")[0]

        all_sites = []
        for site in site_list:
            obj = SiteSchema(
                code=site["SiteCode"],
                name=site["SiteName"],
                status=self._get_status_enum(site["OverallStatus"]),
                latitude=site["Latitude"],
                longitude=site["Longitude"],
                classification=self._get_classification_enum(site["SiteClassification"]),
                source=Source.breathe_london,
                photo_url=site["SitePhotoURL"],
                description=site["SiteDescription"],
                start_date=self._from_isoformat_utc(site["StartDate"]),
                end_date=self._from_isoformat_utc(site["EndDate"]),
                borough=self.borough_mapper.get_borough(site["Latitude"], site["Longitude"]),
            )

            all_sites.append(obj)

        return all_sites

    @staticmethod
    def _to_isoformat_utc(dt):
        # The normal datetime.isoformat() doesn't include the timezone (Z = UTC)
        # so add this now
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _from_isoformat_utc(timestamp: str):
        if timestamp is None:
            return None

        # TODO: handle .000Z
        return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")

    def get_sensor_data(
        self,
        site_code: str,
        start: datetime.datetime,
        end: datetime.datetime,
        series: Series,
    ) -> list[SensorDataSchema]:
        data = self._get(
            f"getClarityData/{site_code}/"
            f"I{series.name.upper()}/"
            f"{BreatheLondon._to_isoformat_utc(start)}/"
            f"{BreatheLondon._to_isoformat_utc(end)}/"
            "Hourly"
        )

        if type(data) == dict:
            # Looks like we get the following returned if there's no data:
            # {
            #     "recordsets": [],
            #     "output": {},
            #     "rowsAffected": [
            #         1,
            #         1,
            #         1,
            #         1
            #     ],
            #     "returnValue": 0
            # }
            return []

        data_schema = []
        for item in data:
            if item["ScaledValue"] is None:
                logging.warning(
                    f"[{site_code}:{series}] Found null data for timestamp {item['DateTime']} - skipping"
                )
                continue

            obj = SensorDataSchema(
                time=datetime.datetime.strptime(item["DateTime"], "%Y-%m-%dT%H:%M:%S.000Z"),
                value=item["ScaledValue"],
            )
            data_schema.append(obj)

        return data_schema