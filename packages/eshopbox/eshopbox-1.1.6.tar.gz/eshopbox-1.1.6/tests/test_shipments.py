import pytest


class TestShipmentsAPI:
    pass

    # def test_create_shipment(self, sdk, mock_token, requests_mock):
    #     requests_mock.post(
    #         "https://test.myeshopbox.com/api/v1/shipments",
    #         json={"shipment_id": "SHIP123"}
    #     )

    #     data = {"order_id": "ORD1"}
    #     result = sdk.shipments.create(data)
    #     assert result["shipment_id"] == "SHIP123"

    # def test_track_shipment(self, sdk, mock_token, requests_mock):
    #     requests_mock.get(
    #         "https://test.myeshopbox.com/api/v1/shipments/SHIP123/track",
    #         json={"status": "in_transit"}
    #     )

    #     tracking = sdk.shipments.track("SHIP123")
    #     assert tracking["status"] == "in_transit"
