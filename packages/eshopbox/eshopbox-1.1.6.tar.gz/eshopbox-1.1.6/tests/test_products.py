import pytest


class TestProductsAPI:
    pass

    # def test_get_products(self, sdk, mock_token, requests_mock):
    #     requests_mock.get(
    #         "https://test.myeshopbox.com/api/v1/products",
    #         json={"products": []}
    #     )

    #     result = sdk.products.get_all()
    #     assert "products" in result

    # def test_get_single_product(self, sdk, mock_token, requests_mock):
    #     requests_mock.get(
    #         "https://test.myeshopbox.com/api/v1/products/SKU123",
    #         json={"sku": "SKU123"}
    #     )

    #     product = sdk.products.get("SKU123")
    #     assert product["sku"] == "SKU123"
