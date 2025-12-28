Wrapper
=======

The **Wrapper** module of the EShopBox SDK provides higher-level methods to manage orders, shipping, returns, tracking, and webhook registration.  

You can use it to:

- Create and manage orders
- Handle shipping and return requests
- Cancel and track shipments
- Register webhooks

Example: Setup Wrapper Using EShopBox SDK
-----------------------------------------

.. code-block:: python

    from eshopbox import EShopBoxSDK
    import os
    from dotenv import load_dotenv
    load_dotenv()


    def order(sdk):
        payload = {
            "channelId": os.getenv('ESHOPBOX_EXTERNAL_CHANNEL_ID'),
            "customerOrderId": "OD119208447831346001",
            "shipmentId": "OD119208447831346001-4380-3659",
            "orderDate": "2024-01-01 09:00:00",
            "isCOD": True,
            "invoiceTotal": 4049.09,
            "shippingMode": "Eshopbox Standard",
            "invoice": {
                "number": "C00011323A000002",
                "date": "2024-01-04 09:00:00"
            },
            ...
        }
        response = sdk.wrapper.order(payload)
        print("Response: ", response)


    def shipping_return(sdk):
        payload = { ... }
        response = sdk.wrapper.shipping_return(payload)
        print("Response: ", response)


    def cancel_tracking(sdk):
        payload = { "trackingId": "1231244" }
        response = sdk.wrapper.cancel_tracking(payload)
        print("Response: ", response)


    def tracking_details(sdk):    
        response = sdk.wrapper.tracking_details("OD119208447831346000-4380-3659")
        print("Response: ", response)


    def webhook_register(sdk):
        payload = {
            "resource": "channel_inventory",
            "eventType": "POST",
            "eventSubType": "updated",
            "version": "v1",
            "externalChannelID": "TEST",
            "webhookUrl": "https://webhook.testurl.com/fake-subscription-url2",
            "webhookMethod": "POST",
            "webhookHeaders": {
                "x-api-key": "test1234",
                "authorization": "Bearer abcdef123456"
            }
        }
        response = sdk.wrapper.webhook_register(payload, ProxyHost="your_proxy_host_value")
        print("Response: ", response)


    def main():
        sdk = EShopBoxSDK(
            workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
            client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
            client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
            refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
        )
        webhook_register(sdk)


    if __name__ == "__main__":
        main()


Wrapper APIs
------------

Order Management
~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.wrapper.order(payload)

Creates an order with shipment, invoice, and product details.

**Required fields in `payload`:**

- `channelId` : string  
- `customerOrderId` : string  
- `shipmentId` : string  
- `orderDate` : string  
- `isCOD` : boolean  
- `invoiceTotal` : float  
- `shippingMode` : string  
- `invoice` : dict  
- `shippingAddress` : dict  
- `items` : list of dict  
- `shipmentDimension` : dict  
- `pickupLocation` : dict  
- `package` : dict

Shipping Returns
~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.wrapper.shipping_return(payload)

Creates a shipping return request with item-level QC details and return dimensions.

Cancel Tracking
~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.wrapper.cancel_tracking(payload)

Cancels a shipment using the `trackingId`.

Tracking Details
~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.wrapper.tracking_details(tracking_id)

Retrieves shipment tracking information.

Webhook Registration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.wrapper.webhook_register(payload, ProxyHost=None)

Registers a webhook for specific events. Optional `ProxyHost` can be provided.

**Webhook payload fields:**

- `resource` : string  
- `eventType` : string (`POST`, `PUT`)  
- `eventSubType` : string (`created`, `updated`)  
- `version` : string  
- `externalChannelID` : string  
- `webhookUrl` : string  
- `webhookMethod` : string (`POST`)  
- `webhookHeaders` : dict (optional)

Notes
-----

- Always provide valid workspace credentials using environment variables.  
- Ensure webhook URLs are publicly accessible and accept HTTP requests.  
- Orders and shipments must include accurate product, address, and dimension details.  
- Use the Wrapper module for higher-level workflow automation over basic SDK endpoints.

