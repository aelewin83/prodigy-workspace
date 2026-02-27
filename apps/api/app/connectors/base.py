from __future__ import annotations

from dataclasses import dataclass

from app.services.comps import NormalizedCompRow


@dataclass
class ConnectorRateLimit:
    requests_per_minute: int


class BaseConnector:
    connector_id: str
    name: str
    domain_or_dataset: str
    allowlisted: bool
    rate_limit: ConnectorRateLimit

    def fetch(self, filters: dict) -> list[dict]:
        raise NotImplementedError

    def parse(self, raw_items: list[dict]) -> list[NormalizedCompRow]:
        raise NotImplementedError
