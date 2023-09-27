import pydash


class Enricher:
    @staticmethod
    def enrich(site_metadata, site_data):
        for site in site_metadata:
            # Find the value in the list of data
            data_row = pydash.collections.find(
                site_data, lambda row: row["site_code"] == site["SiteCode"]
            )

            if data_row is not None:
                site["value"] = data_row["value"]
            else:
                site["value"] = None

        return site_metadata
