Shipments
=========

The **Shipments** module of the EShopBox SDK allows you to:

- Retrieve all shipments  
- Fetch a specific shipment  
- Create a shipment  
- Update shipment status  

This page shows how to interact with the Shipments API through the Python SDK.

Example: Track Shipment Using EShopBox SDK
------------------------------------------

.. code-block:: python

    """
    Example: Track shipment using EShopBox SDK
    """

    from eshopbox import EShopBoxSDK
    import os
    from dotenv import load_dotenv
    load_dotenv()


    def get_all_shipments(sdk):
        shipments = sdk.shipments.get_all()
        print(shipments)


    def get_shipment(sdk):
        shipment = sdk.shipments.get("OD119208447831346000-4380-3659")
        print(shipment)


    def create_shipment(sdk):
        payload = {
            "customerOrderNumber": "OD119208447831346000",
            "vendorOrderNumber": "OD119208447831346000",
            "externalShipmentID": "300884672-5-87",
            "externalWarehouseID": "W4585",
            "externalChannelID": "{{externalChannelID}}",
            "defaultWarehouseCode": "2022",
            "orderDate": "2020-03-18 15:52:38",
            "portal_id": 12,
            "paymentType": "COD",
            "expectedShipDate": None,
            "externalManifestNumber": None,
            "channelManifestNumber": None,
            "order_id": 1576882,
            "channel_id": 271,
            "warehouse_id": 21,
            "channel_account_id": None,
            "account_id": 6,
            "region": "Local",
            "picklistCode": None,
            "invoiceNumber": "SESI1687",
            "boxType": "UNKNOWN",
            "isPriorityShipment": "0",
            "isGift": "0",
            "invoice_url": "",
            "invoiceDate": "2020-03-19 00:00:00",
            "label_url": "https://pyck-res-bucket.s3.amazonaws.com:443/DELHIVERY/2020-03-18/2098310486496.pdf",
            "labels": "",
            "shippingInfo": [],
            "boxAdditionalRecommendation": [],
            "dimension_length": "10",
            "dimension_width": "20",
            "dimension_height": "12",
            "weight": "1231",
            "trackingID": "2098310486496",
            "packageID": "",
            "barcode": "",
            "courierName": "Delhivery",
            "created_at": "2020-03-18 21:22:57",
            "updated_at": "2020-03-19 01:54:20",
            "status": "intransit",
            "remarks": "shipment picked up from client location",
            "customerName": "Sakib Malik",
            "customerContactNumber": "xxxxxxxxxx",
            "email": "xxxxxxxxxxxxxxx@gmail.com",
            "channelSlug": "blackberrys",
            "status_updated_at": "2020-03-19 14:50:29",
            "status_log": {
                "intransit": "2020-03-19 14:50:29",
                "dispatched": "2020-03-19 06:30:34",
                "packed": "2020-03-19 01:54:23",
                "created": "2020-03-18 21:22:57"
            },
            "orderExternalCreatedAt": "2020-03-18 21:22:52",
            "shippingAddress": {
                "customerName": "Sakib Malik",
                "addressLine1": "D151",
                "addressLine2": "industrail Area",
                "city": "Mohali",
                "state": "Punjab",
                "postalCode": "160071",
                "countryCode": "IN",
                "countryName": "India",
                "contactPhone": "xxxxxxxxxx",
                "email": "xxxxxxxxxxxxxxx@gmail.com"
            },
            "id": 1583574,
            "isCOD": "1",
            "track_payload": {
                "clickPostTrackData": {
                    "status": "In Transit",
                    "clickpost_status_description": "InTransit",
                    "waybill": "2098310486496",
                    "account_code": "Delhivery Surface",
                    "location": "Gurgaon_Bilaspur_P (Haryana)",
                    "clickpost_status_code": 5,
                    "remark": "Shipment Picked Up from Client Location",
                    "cp_id": 4,
                    "timestamp": "2020-03-19T13:48:28Z",
                    "additional": {
                        "latest_status": {
                            "clickpost_status_bucket_description": "In transit",
                            "clickpost_status_description": "InTransit",
                            "reference_number": "BLCK103443-271-49",
                            "clickpost_status_bucket": 3,
                            "status": "In Transit",
                            "location": "Gurgaon_Bilaspur_P (Haryana)",
                            "clickpost_status_code": 5,
                            "remark": "Shipment Picked Up from Client Location",
                            "timestamp": "2020-03-19T13:48:28Z"
                        },
                        "destination_hub_inscan_ts": None,
                        "courier_partner_edd": None,
                        "is_rvp": None
                    }
                }
            },
            "packed_date": "2020-03-19 01:54:23",
            "items": [
                {
                    "id": 49252802,
                    "lineItemSequenceNumber": 112988,
                    "orderItemID": "OD119208447831346000-49252802",
                    "itemID": "DB9U03FMGWZ",
                    "sku": "2316W3I7KID",
                    "productName": "Pace Barnes",
                    "quantity": 1,
                    "customerPrice": 4499,
                    "discount": 449.89,
                    "lineItemTotal": 4049.09,
                    "taxRate": 12,
                    "taxAmount": 0,
                    "giftMessage": "",
                    "giftLabelContent": "",
                    "cancellationReason": "",
                    "cancellationTime": "0000-00-00 00:00:00",
                    "original_order_item_id": None,
                    "isVirtualKit": "0",
                    "productAdditionalInfo": {
                        "size": None,
                        "color": None,
                        "weight": 20.99,
                        "height": 12.13,
                        "length": 11.13,
                        "width": 8.13,
                        "taxPercentage": 12,
                        "hsnCode": "HSN1324",
                        "productDetails": {
                            "hsnCode": "HSN1324",
                            "dimensionHeight": 12.13,
                            "dimensionLength": 11.13,
                            "description": "Pace Barnes",
                            "weight": 20.99,
                            "mrp": 6000,
                            "dimensionWidth": 8.13,
                            "type": "BASE",
                            "taxCode": "ESBGST9",
                            "imageUrl": "https://s3.../1.JPG",
                            "accountSlug": "kashwork-ecommerce",
                            "sku": "ABD-123",
                            "esin": "2316W3I7KID",
                            "status": "DRAFT",
                            "weightUnit": "g"
                        }
                    },
                    "productImageUrl": "https://s3.../1.JPG",
                    "productUrl": "...",
                    "invoiceTotal": 4049.09,
                    "shippingCharges": 0,
                    "giftWrapCharges": 0,
                    "cashOnDeliveryCharges": 0
                }
            ]
        }
        shipment = sdk.shipments.create(payload)
        print(shipment)


    def update(sdk):
        shipment = sdk.shipments.update("OD119208447831346000-4380-3659", "dispatched")
        print(shipment)


    def main():
        sdk = EShopBoxSDK(
            workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
            client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
            client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
            refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
        )
        update(sdk)


    if __name__ == "__main__":
        main()


Shipment APIs
-------------

Get All Shipments
~~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.shipments.get_all()

Returns a list of all shipments tied to the workspace.


Get a Single Shipment
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.shipments.get(shipment_id)

Retrieves details for a specific shipment.

Example:

.. code-block:: python

    sdk.shipments.get("OD119208447831346000-4380-3659")


Create a Shipment
~~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.shipments.create(payload)

Creates a shipment in EShopBox.

Payload includes:

- Order details (internal/external IDs)
- Shipping address
- Invoice information
- Dimensions & weight
- Tracking details
- Item-level product information


Update Shipment Status
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.shipments.update(shipment_id, status)

Updates the status of a shipment.

Example:

.. code-block:: python

    sdk.shipments.update("OD119208447831346000-4380-3659", "dispatched")


Notes
-----

- Shipment creation requires valid customer, item, and address records.
- Use tracking IDs to sync with courier partners.
- Status updates should follow valid status transitions (e.g., `packed → dispatched → intransit → delivered`).
- Always store your SDK credentials using environment variables.

