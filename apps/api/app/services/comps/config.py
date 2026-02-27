from dataclasses import dataclass


@dataclass(frozen=True)
class CompsConfig:
    allowlisted_connectors: tuple[str, ...] = (
        "example_public_dataset",
        "example_public_web",
    )
    allowlisted_domains: tuple[str, ...] = (
        "data.cityofnewyork.us",
        "example.com",
    )
    default_rpm: int = 30
    default_window_days: int = 180
