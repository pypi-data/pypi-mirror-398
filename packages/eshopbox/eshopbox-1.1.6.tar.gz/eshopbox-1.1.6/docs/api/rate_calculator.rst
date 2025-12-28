Rate Calculator
===============

The Rate Calculator API allows you to compute shipping charges based on 
origin/destination pincodes, weight, dimensions, journey type, and payment mode.

This guide explains how to initialize the EShopBox SDK and use the 
``rate_calculator`` interface.

Example: Setup Rate Calculator Using EShopBox SDK
-------------------------------------------------

The following code demonstrates how to authenticate with EShopBox and calculate rates:

.. code-block:: python

    """
    Example: Setup Rate Calculator using EShopBox SDK
    """

    import os
    from eshopbox.client import EShopBoxSDK
    from dotenv import load_dotenv
    load_dotenv()


    def rate_calculator(sdk):
        payload = {
            "journeyType": "forward",
            "pickupPincode": "160071",
            "dropPincode": "247342",
            "orderWeight": "500",
            "length": "12",
            "width": "12",
            "height": "33",
            "paymentMethod": "Prepaid",
            "doorstepQc": False
        }
        response = sdk.rate_calculator.calculate(payload)
        print("Response: ", response)


    def main():
        sdk = EShopBoxSDK(
            workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
            client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
            client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
            refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
        )
        rate_calculator(sdk)


    if __name__ == "__main__":
        main()


Parameters
----------

The ``rate_calculator.calculate(payload)`` method accepts the following fields:

+------------------+----------+----------+--------------------------------------------------+
| Field            | Type     | Required | Description                                      |
+==================+==========+==========+==================================================+
| journeyType      | string   | Yes      | The journey type. Allowed: ``forward``, ``reverse`` |
+------------------+----------+----------+--------------------------------------------------+
| pickupPincode    | string   | Yes      | Origin pincode                                   |
+------------------+----------+----------+--------------------------------------------------+
| dropPincode      | string   | Yes      | Destination pincode                              |
+------------------+----------+----------+--------------------------------------------------+
| orderWeight      | string   | Yes      | Weight of shipment (grams)                       |
+------------------+----------+----------+--------------------------------------------------+
| length           | string   | Yes      | Package length in cm                             |
+------------------+----------+----------+--------------------------------------------------+
| width            | string   | Yes      | Package width in cm                              |
+------------------+----------+----------+--------------------------------------------------+
| height           | string   | Yes      | Package height in cm                             |
+------------------+----------+----------+--------------------------------------------------+
| paymentMethod    | string   | Yes      | ``Prepaid`` or ``COD``                           |
+------------------+----------+----------+--------------------------------------------------+
| doorstepQc       | boolean  | No       | Perform doorstep QC (default: ``False``)         |
+------------------+----------+----------+--------------------------------------------------+


Response Format
----------------

A successful API response typically returns shipping charges and service details.

Example response:

.. code-block:: json

    {
        "data": {
            "total_charges": 120.5,
            "carrier": "Delhivery",
            "service_type": "Surface",
            "estimated_delivery_days": 4
        }
    }


Notes
-----

- Ensure your environment variables include:

  - ``ESHOPBOX_WORKSPACE``
  - ``ESHOPBOX_CLIENT_ID``
  - ``ESHOPBOX_SECRET_ID``
  - ``ESHOPBOX_REFRESH_TOKEN``

- The rate returned depends on carrier availability, weight slabs, and payment method.
- Pincodes must be valid and serviceable for the journey type.

