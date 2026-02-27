from datetime import date

from app.connectors.base import BaseConnector, ConnectorRateLimit
from app.models.enums import ListingSourceType
from app.services.comps import build_normalized_row


class SamplePublicConnector(BaseConnector):
    connector_id = "sample_public_connector"
    name = "Sample Public Connector"
    domain_or_dataset = "data.example.com"
    allowlisted = True
    rate_limit = ConnectorRateLimit(requests_per_minute=30)

    def fetch(self, filters: dict) -> list[dict]:
        # Deterministic seed payload used until real provider integration is added.
        return [
            {
                "address": "100 Main St, Brooklyn, NY",
                "unit": "2A",
                "beds": 1,
                "baths": 1,
                "rent": 3150,
                "gross_rent": 3300,
                "date_observed": date(2026, 2, 1),
                "link": "https://data.example.com/listing/100-main-2a",
            }
        ]

    def parse(self, raw_items: list[dict]):
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
                    notes="sample connector row",
                    source_type=ListingSourceType.PUBLIC_DATASET,
                    source_ref=item.get("link"),
                    confidence_score=0.8,
                )
            )
        return rows
