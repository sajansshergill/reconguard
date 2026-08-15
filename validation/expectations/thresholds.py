"""Load expectation thresholds from config."""
import yaml


def load_expectations(path: str = "config/expectations.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)