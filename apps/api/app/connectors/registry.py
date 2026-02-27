from app.connectors.base import BaseConnector
from app.connectors.sample_public_connector import SamplePublicConnector


def get_connectors() -> dict[str, BaseConnector]:
    connector_instances = [SamplePublicConnector()]
    return {c.connector_id: c for c in connector_instances}
