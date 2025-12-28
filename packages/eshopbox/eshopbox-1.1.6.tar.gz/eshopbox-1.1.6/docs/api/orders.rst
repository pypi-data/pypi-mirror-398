.. _orders_api:

=====================
Order Management
=====================

The EShopBox SDK provides APIs to create, retrieve, cancel, and manage customer
orders from your workspace. This page explains all order-related operations with
complete examples.

Before using the orders API, ensure the SDK is initialized with valid
credentials.

------------------------
Basic Usage Example
------------------------

Below is a complete working script demonstrating all available order
operations via the EShopBox SDK.

.. code-block:: python

    """
    Example: Setup order using EShopBox SDK
    """

    from eshopbox import EShopBoxSDK
    import os
    from dotenv import load_dotenv
    load_dotenv()


    def get_all_orders(sdk):
        params = {
            'filters': 'account=kashwork-ecommerce'
        }
        response = sdk.orders.get_all(page=1, **params)
        print("Response: ", response)


    def get_order(sdk):
        response = sdk.orders.get('OD119208447831346001')
        print("Response: ", response)


    def create_order(sdk):
        order = {
            "externalChannelID": os.getenv('ESHOPBOX_EXTERNAL_CHANNEL_ID'),
            "customerOrderNumber": "OD119208447831346002",
            "orderDate": "2020-02-29 15:39:11",
            "isCOD": "0",
            "paymentType": "DebitCard",
            "shipChargeAmount": 0,
            "subtotal": 4049.09,
            "orderTotal": 4049.09,
            "balanceDue": 0,
            "thirdPartyShipping": False,
            "shippingAddress": {
                "customerName": "Sakib Malik",
                "addressLine1": "D151",
                "addressLine2": "industrail Area",
                "city": "mohali",
                "state": "Punjab",
                "postalCode": "160071",
                "gstin": "27ABCGN5397X1XX",
                "countryCode": "IN",
                "countryName": "India",
                "contactPhone": "xxxxxxxxxx",
                "email": "xxxxxxxxxxxxxxx@gmail.com"
            },
            "billingAddress": {
                "customerName": "Sakib Malik",
                "addressLine1": "D151",
                "addressLine2": "industrail Area",
                "city": "mohali",
                "state": "Punjab",
                "postalCode": "160071",
                "countryCode": "IN",
                "countryName": "India",
                "contactPhone": "xxxxxxxxxx",
                "email": "xxxxxxxxxxxxxxx@gmail.com"
            },
            "items": [
                {
                    "lineItemSequenceNumber": 100,
                    "itemID": "KW-100",
                    "sellerSkuOnChannel": "KW-123",
                    "productName": "Keyboard",
                    "quantity": 1,
                    "customerPrice": 4499,
                    "discount": 449.89,
                    "lineItemTotal": 4049.09,
                    "mrp": 6000,
                    "productAdditionalInfo": {
                        "size": "",
                        "color": "",
                        "weight": 20.99,
                        "height": 12.13,
                        "length": 11.13,
                        "width": 8.13,
                        "taxPercentage": 12.00,
                        "hsnCode": "HSN1324"
                    },
                    "productUrl": "https://kashwork.com/d/jewellery/imitation_jewellery/women_imitation_jewellery_/women_necklace_sets/dabka_jewellery_set/161291130/598744146",
                    "productImageUrl": "https://kw-live.s3.amazonaws.com/media/post_images/upload/product_pic_d4bda7fb-e2f1-4061-b2ef-e4a5bd7618b8.webp"
                }
            ]
        }
        response = sdk.orders.create(order)
        print("Response: ", response)


    def cancel_order(sdk):
        cancel_data = {
            "externalChannelID": os.getenv('ESHOPBOX_EXTERNAL_CHANNEL_ID'),
            "customerOrderNumber": "OD119208447831346002",
            "actor": "xxxxxxxxxxxxxxx@gmail.com",
            "reason": "Cancelled By Customer",
            "cancellationTime": "2018-07-08 22:00:05",
            "items": [
                {
                    "lineItemSequenceNumber": 100,
                    "itemID": "KW-100",
                    "quantity": 1,
                    "productName": "Keyboard",
                    "remark": "cancelled by customer"
                }
            ]
        }
        response = sdk.orders.cancel(cancel_data)
        print("Response: ", response)


    def get_invoice(sdk):
        response = sdk.orders.get_invoice('OD119208447831346002')
        print("Response: ", response)


    def main():
        sdk = EShopBoxSDK(
            workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
            client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
            client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
            refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
        )

        # get_all_orders(sdk)
        # get_order(sdk)
        # create_order(sdk)
        # cancel_order(sdk)
        get_invoice(sdk)

    if __name__ == "__main__":
        main()

------------------------
API Reference
------------------------

Get All Orders
==============

**Method**

``sdk.orders.get_all(page: int = 1, **filters)``

**Description**

Fetch a paginated list of orders.

**Example**

.. code-block:: python

    orders = sdk.orders.get_all(page=1, filters="account=kashwork-ecommerce")
    print(orders)


Get Single Order
================

**Method**

``sdk.orders.get(order_id: str)``

**Example**

.. code-block:: python

    order = sdk.orders.get("OD119208447831346001")
    print(order)


Create Order
============

**Method**

``sdk.orders.create(order_payload: dict)``

Full payload example is included above.

**Example**

.. code-block:: python

    response = sdk.orders.create(order)
    print(response)


Cancel Order
============

**Method**

``sdk.orders.cancel(cancel_payload: dict)``

**Example**

.. code-block:: python

    response = sdk.orders.cancel(cancel_data)
    print(response)


Get Invoice
===========

**Method**

``sdk.orders.get_invoice(order_id: str)``

**Example**

.. code-block:: python

    invoice = sdk.orders.get_invoice("OD119208447831346002")
    print(invoice)

------------------------
Environment Variables
------------------------

Store credentials in a `.env` file:

.. code-block:: bash

    ESHOPBOX_WORKSPACE="your-workspace"
    ESHOPBOX_CLIENT_ID="your-client-id"
    ESHOPBOX_SECRET_ID="your-secret-id"
    ESHOPBOX_REFRESH_TOKEN="your-refresh-token"
    ESHOPBOX_EXTERNAL_CHANNEL_ID="your-channel-id"

------------------------
Next Steps
------------------------

- See :ref:`inventory_api` to manage stock levels.
- See :ref:`products_api` to manage your catalog.
