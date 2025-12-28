import pytest
from eshopbox import EShopBoxSDK


@pytest.fixture
def sdk():
    return EShopBoxSDK(
        workspace="test",
        client_id="test_id",
        client_secret="test_secret",
        refresh_token="test_refresh_token",
    )


@pytest.fixture
def mock_token(requests_mock):
    """Mocks auth token request."""
    requests_mock.post(
        "https://auth.myeshopbox.com/api/v1/generateToken",
        json={"access_token": "mock_access_token"}
    )
