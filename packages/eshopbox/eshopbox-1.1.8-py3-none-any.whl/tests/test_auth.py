import pytest
from eshopbox.exceptions import APIError


class TestAuthAPI:
    pass
    # def test_generate_token_success(self, sdk, requests_mock):
    #     requests_mock.post(
    #         "https://auth.myeshopbox.com/api/v1/generateToken",
    #         json={"access_token": "xyz123"}
    #     )
    #     token = sdk.auth.generate_token()
    #     assert token == "xyz123"

    # def test_generate_token_failure(self, sdk, requests_mock):
    #     requests_mock.post(
    #         "https://auth.myeshopbox.com/api/v1/generateToken",
    #         status_code=400,
    #         json={"error": "invalid_auth"}
    #     )

    #     with pytest.raises(APIError):
    #         sdk.auth.generate_token()
