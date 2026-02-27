from datetime import date

from app.models.enums import ListingSourceType
from app.services.comps.connector_base import ConnectorRateLimit
from app.services.comps.normalize import build_normalized_row


class ExamplePublicDatasetConnector:
    connector_id = "example_public_dataset"
    display_name = "Example Public Dataset"
    source_type = "public_dataset"
    domains = ("data.cityofnewyork.us",)
    rate_limit = ConnectorRateLimit(requests_per_minute=30)

    def fetch_raw(self, query: dict) -> list[dict]:
        return [
            {
                "address": "100 Main St, Brooklyn, NY",
                "unit": "2A",
                "beds": 1,
                "baths": 1,
                "rent": 3150,
                "gross_rent": 3300,
                "date_observed": date(2026, 2, 1),
                "link": "https://data.cityofnewyork.us/resource/demo",
            }
        ]

    def parse_raw_to_rows(self, raw_items: list[dict], query: dict):
        rows = []
        for item in raw_items:
            rows.append(
                build_normalized_row(
                    address=item["address"],
                    unit=item.get("unit"),
                    beds=float(item["beds"]) if item.get("beds") is not None else None,
                    baths=float(item["baths"]) if item.get("baths") is not None else None,
                    rent=float(item["rent"]) if item.get("rent") is not None else None,
                    gross_rent=float(item["gross_rent"]) if item.get("gross_rent") is not None else None,
                    date_observed=item.get("date_observed"),
                    link=item.get("link"),
                    notes="dataset sample row",
                    source_type=ListingSourceType.PUBLIC_DATASET,
                    source_ref=item.get("link"),
                    confidence_score=0.8,
                )
            )
        return rows
