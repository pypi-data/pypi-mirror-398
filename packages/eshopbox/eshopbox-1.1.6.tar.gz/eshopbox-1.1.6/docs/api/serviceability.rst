Serviceability
==============

The Serviceability API allows you to validate whether a shipment or product can be serviced between a given pickup and delivery pincode.  
It provides multiple methods:

- Pincode-based serviceability  
- Product-based serviceability  
- Check serviceability for pickup/delivery combination  
- Bulk pincode serviceability

This page demonstrates how to use each method via the EShopBox Python SDK.

Example: Setup Serviceability Using EShopBox SDK
------------------------------------------------

.. code-block:: python

    """
    Example: Setup Serviceability using EShopBox SDK
    """

    import os
    from eshopbox.client import EShopBoxSDK
    from dotenv import load_dotenv
    load_dotenv()


    def get_serviceability_pin_code_based(sdk):
        payload = {
            "dropPincode": "160071",
            "pickupPincode": "247342",
            "deadWeight": 500,
            "length": 12,
            "height": 10,
            "width": 8,
            "isCod": False
        }
        response = sdk.serviceability.pincodeserviceability(payload)
        print("Response: ", response)


    def get_productserviceability(sdk):
        payload = {
            "dropPincode": "160071",
            "productId": "sakib"
        }
        response = sdk.serviceability.productserviceability(payload)
        print("Response: ", response)


    def get_checkpincodeserviceability(sdk):
        payload = {
            "deliveryPincode": "160071",
            "pickupPincode": "247342"
        }
        response = sdk.serviceability.checkpincodeserviceability(payload)
        print("Response: ", response)


    def get_get_bulk_pin_code_serviceability(sdk):
        params = {
            "shippingMode": "standard"
        }
        response = sdk.serviceability.bulkPincodeServiceability(params)
        print("Response: ", response)


    def main():
        sdk = EShopBoxSDK(
            workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
            client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
            client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
            refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
        )
        # get_serviceability_pin_code_based(sdk)
        # get_productserviceability(sdk)
        # get_checkpincodeserviceability(sdk)
        get_get_bulk_pin_code_serviceability(sdk)


    if __name__ == "__main__":
        main()


Pincode-Based Serviceability
----------------------------

Checks whether a shipment with given dimensions, weight, and payment mode  
can be serviced between two pincodes.

**Payload Fields**

+------------------+----------+----------+----------------------------------------+
| Field            | Type     | Required | Description                            |
+==================+==========+==========+========================================+
| dropPincode      | string   | Yes      | Destination pincode                    |
+------------------+----------+----------+----------------------------------------+
| pickupPincode    | string   | Yes      | Origin pincode                         |
+------------------+----------+----------+----------------------------------------+
| deadWeight       | integer  | Yes      | Weight in grams                        |
+------------------+----------+----------+----------------------------------------+
| length           | integer  | Yes      | Package length in cm                   |
+------------------+----------+----------+----------------------------------------+
| height           | integer  | Yes      | Package height in cm                   |
+------------------+----------+----------+----------------------------------------+
| width            | integer  | Yes      | Package width in cm                    |
+------------------+----------+----------+----------------------------------------+
| isCod            | boolean  | Yes      | COD allowed or not                     |
+------------------+----------+----------+----------------------------------------+

Example Response:

.. code-block:: json

    {
        "serviceable": true,
        "carrier": "Delhivery",
        "est_delivery_days": 3
    }


Product-Based Serviceability
----------------------------

Checks whether a specific product can be delivered to a destination pincode.

**Payload Fields**

+-------------+----------+----------+--------------------------------------------+
| Field       | Type     | Required | Description                                |
+=============+==========+==========+============================================+
| dropPincode | string   | Yes      | Destination pincode                        |
+-------------+----------+----------+--------------------------------------------+
| productId   | string   | Yes      | Unique identifier of the product           |
+-------------+----------+----------+--------------------------------------------+

Example Response:

.. code-block:: json

    {
        "productId": "sakib",
        "serviceable": true,
        "carrier": "BlueDart"
    }


Check Pickup/Delivery Serviceability
------------------------------------

Validates serviceability for a pickup and delivery pincode combination.

**Payload Fields**

+------------------+----------+----------+--------------------------------------------+
| Field            | Type     | Required | Description                                |
+==================+==========+==========+============================================+
| deliveryPincode  | string   | Yes      | Destination pincode                        |
+------------------+----------+----------+--------------------------------------------+
| pickupPincode    | string   | Yes      | Origin pincode                             |
+------------------+----------+----------+--------------------------------------------+

Example Response:

.. code-block:: json

    {
        "pickupPincode": "247342",
        "deliveryPincode": "160071",
        "serviceable": true
    }


Bulk Pincode Serviceability
---------------------------

Fetches serviceability details for multiple pincodes at once.

**Query Parameters**

+----------------+----------+----------+------------------------------+
| Field          | Type     | Required | Description                  |
+================+==========+==========+==============================+
| shippingMode   | string   | Yes      | Mode of shipping (e.g.      |
|                |          |          | ``standard``, ``express``)   |
+----------------+----------+----------+------------------------------+

Example Response:

.. code-block:: json

    {
        "shippingMode": "standard",
        "serviceablePincodes": [
            "160071",
            "247342",
            "110001"
        ]
    }


Notes
-----

- Ensure valid API credentials are stored in your environment variables.
- Serviceability results vary by carrier availability, service type, and region.
- You may call any of the serviceability functions independently as needed.

