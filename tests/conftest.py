import os

import pytest

BASE_URL = os.environ.get("SERVICE_BASE_URL", "http://localhost:8083")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL
