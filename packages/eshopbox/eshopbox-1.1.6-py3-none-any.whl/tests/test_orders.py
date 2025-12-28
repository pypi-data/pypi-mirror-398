
import pytest
from eshopbox import EShopBoxSDK
from eshopbox.exceptions import APIError, ValidationError


class TestOrdersAPI:

    @pytest.fixture
    def sdk(self):
        return EShopBoxSDK(
            workspace="test",
            client_id="test_id",
            client_secret="test_secret",
            refresh_token="test_token"
        )

    def test_get_all_orders(self, sdk, requests_mock):
        requests_mock.post(
            "https://auth.myeshopbox.com/api/v1/generateToken",
            json={"access_token": "test_token"}
        )
        requests_mock.get(
            "https://test.myeshopbox.com/api/v1/orders/erp",
            json={"orders": []}
        )

        result = sdk.orders.get_all()
        assert "orders" in result

    def test_create_order(self, sdk, requests_mock):
        # Test implementation...
        pass
