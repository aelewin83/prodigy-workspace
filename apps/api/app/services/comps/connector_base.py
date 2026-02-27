from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.services.comps.normalize import NormalizedCompRow


@dataclass
class ConnectorRateLimit:
    requests_per_minute: int


class CompConnector(Protocol):
    connector_id: str
    display_name: str
    source_type: str
    domains: tuple[str, ...]

    def fetch_raw(self, query: dict) -> list[dict]:
        ...

    def parse_raw_to_rows(self, raw_items: list[dict], query: dict) -> list[NormalizedCompRow]:
        ...
