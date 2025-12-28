class TestWorkflowIntegration:
    pass

    # def test_full_order_flow(self, sdk, requests_mock):
    #     # mock token
    #     requests_mock.post(
    #         "https://auth.myeshopbox.com/api/v1/generateToken",
    #         json={"access_token": "token123"}
    #     )

    #     # 1. Create Order
    #     requests_mock.post(
    #         "https://test.myeshopbox.com/api/v1/orders",
    #         json={"order_id": "O1"}
    #     )

    #     # 2. Create Shipment
    #     requests_mock.post(
    #         "https://test.myeshopbox.com/api/v1/shipments",
    #         json={"shipment_id": "S1"}
    #     )

    #     # 3. Track
    #     requests_mock.get(
    #         "https://test.myeshopbox.com/api/v1/shipments/S1/track",
    #         json={"status": "shipped"}
    #     )

    #     order = sdk.orders.create({"order_number": "123"})
    #     shipment = sdk.shipments.create({"order_id": order["order_id"]})
    #     tracking = sdk.shipments.track(shipment["shipment_id"])

    #     assert tracking["status"] == "shipped"
