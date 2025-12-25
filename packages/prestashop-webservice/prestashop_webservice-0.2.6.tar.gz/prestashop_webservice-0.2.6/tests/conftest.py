import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from prestashop_webservice import Client


@pytest.fixture(scope="session")
def load_test_env():
    """Load test environment variables."""
    env_path = Path(__file__).parent.parent / ".env.test"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        pytest.skip("No .env.test file found")


@pytest.fixture(scope="session")
def prestashop_base_url(load_test_env):
    """Get PrestaShop base URL from environment."""
    url = os.getenv("PRESTASHOP_BASE_URL")
    if not url:
        pytest.skip("PRESTASHOP_BASE_URL not set")
    return url


@pytest.fixture(scope="session")
def prestashop_ws_key(load_test_env):
    """Get PrestaShop web service key from environment."""
    key = os.getenv("PRESTASHOP_WS_KEY")
    if not key:
        pytest.skip("PRESTASHOP_WS_KEY not set")
    return key


@pytest.fixture(scope="session")
def client(prestashop_base_url, prestashop_ws_key):
    """Create a PrestaShop client instance."""
    return Client(
        prestashop_base_url=prestashop_base_url,
        prestashop_ws_key=prestashop_ws_key,
        max_connections=2,
        max_keepalive_connections=2,
        keepalive_expiry=10.0,
    )
