from app.services.comps.connector_base import CompConnector
from app.services.comps.connectors.example_public_dataset import ExamplePublicDatasetConnector
from app.services.comps.connectors.example_public_web import ExamplePublicWebConnector


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, CompConnector] = {}

    def register(self, connector: CompConnector) -> None:
        self._connectors[connector.connector_id] = connector

    def get(self, connector_id: str) -> CompConnector:
        if connector_id not in self._connectors:
            raise KeyError(f"Unknown connector_id: {connector_id}")
        return self._connectors[connector_id]

    def list_ids(self) -> list[str]:
        return sorted(self._connectors.keys())


REGISTRY = ConnectorRegistry()
REGISTRY.register(ExamplePublicDatasetConnector())
REGISTRY.register(ExamplePublicWebConnector())
