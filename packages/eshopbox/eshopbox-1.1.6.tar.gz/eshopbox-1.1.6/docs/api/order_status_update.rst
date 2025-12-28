.. _order_status_update_api:

=========================================
Order Status Update & Shipment Tracking
=========================================

The ``order_status_update`` module in the EShopBox SDK allows you to:

- Generate labels & AWB numbers  
- Fetch courier names and assigned AWB  
- Dispatch shipments  
- Track return shipment courier details  
- Update order delivery statuses (Delivered, In Transit, RTO, Lost, etc.)

This page includes full examples and API method references.

------------------------------
Basic Usage Example
------------------------------

Below is a complete example demonstrating all functions of the
``order_status_update`` API.

.. code-block:: python

    """
    Example: Track shipment using EShopBox SDK
    """

    from eshopbox import EShopBoxSDK
    import os
    from dotenv import load_dotenv
    load_dotenv()


    def create_label_and_awb(sdk):
        payload = {
            "boxHeight": 2,
            "boxLength": 2,
            "boxWidth": 2,
            "weight": 2,
            "orderItems": [
                {
                    "orderItemId": "49252941",
                    "invoiceNumber": "string",
                    "invoiceDate": "2017-01-02T08:12:53",
                    "taxRate": 0,
                    "centralGstPercentage": 0,
                    "compensationCessPercentage": 0,
                    "integratedGstPercentage": 0,
                    "stateGstPercentage": 0,
                    "unionTerritoryGstPercentage": 0
                }
            ]
        }
        response = sdk.order_status_update.create_label_and_awb(payload)
        print(response)


    def get_awb_and_courier_name(sdk):
        params = {
            "orderItemIds": "49252941,49252802"
        }
        response = sdk.order_status_update.get_awb_and_courier_name(params)
        print(response)


    def dispatch_shipment(sdk):
        payload = {
            "orderItems": [
                {
                    "orderItemId": "49252941",
                    "quantity": 1,
                    "centralGstPercentage": 0,
                    "compensationCessPercentage": 0,
                    "integratedGstPercentage": 0,
                    "stateGstPercentage": 0,
                    "taxRate": 0,
                    "unionTerritoryGstPercentage": 0
                }
            ],
            "selfShipping": {
                "deliveryPartner": "ecomExpress",
                "dispatchDate": "2017-01-02T08:12:53",
                "invoiceDate": "2017-01-02T08:12:53",
                "invoiceNumber": "string",
                "tentativeDeliveryDate": "2017-01-02T08:12:53",
                "trackingId": "123455"
            }
        }
        response = sdk.order_status_update.dispatch_shipment(payload)
        print(response)


    def courier_details_for_return(sdk):
        response = sdk.order_status_update.courier_details_for_return("R2113455")
        print(response)


    def update(sdk):
        payload = {
            "status_description": "Delivered",
            "waybill": "1704610028453",
            "cp_name": "Delhivery",
            "status": "Delivered",
            "status_code": 8,
            "location": "GGN_DPC (Haryana)",
            "additional": {
                "latest_status": {
                    "status_description": "Delivered",
                    "remark": "Added to IST",
                    "status": "In Transit",
                    "status_code": 8,
                    "location": "GGN_DPC (Haryana)",
                    "timestamp": "2018-07-12T12:58:40.910000Z"
                }
            },
            "timestamp": "2018-07-12T11:53:39.902000Z",
            "remark": "Bagged at destination city PC"
        }
        response = sdk.order_status_update.update(payload)
        print(response)


    def main():
        sdk = EShopBoxSDK(
            workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
            client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
            client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
            refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
        )

        # create_label_and_awb(sdk)
        # get_awb_and_courier_name(sdk)
        # dispatch_shipment(sdk)
        # courier_details_for_return(sdk)
        update(sdk)


    if __name__ == "__main__":
        main()

-------------------------
API Reference
-------------------------

Create Label & AWB
===================

**Method**

``sdk.order_status_update.create_label_and_awb(payload: dict)``

**Purpose**

Generates:

- Shipping label  
- AWB (Air Waybill) number  
- Invoice details for shipment  

**Example**

.. code-block:: python

    response = sdk.order_status_update.create_label_and_awb(payload)


Get AWB & Courier Name
=======================

**Method**

``sdk.order_status_update.get_awb_and_courier_name(params: dict)``

**Example**

.. code-block:: python

    sdk.order_status_update.get_awb_and_courier_name({
        "orderItemIds": "49252941,49252802"
    })


Dispatch Shipment
=================

**Method**

``sdk.order_status_update.dispatch_shipment(payload: dict)``

Marks shipment as dispatched with courier details.

**Example**

.. code-block:: python

    response = sdk.order_status_update.dispatch_shipment(payload)


Courier Details for Return
==========================

**Method**

``sdk.order_status_update.courier_details_for_return(return_id: str)``

Fetches courier partner and AWB for return pickup.

**Example**

.. code-block:: python

    details = sdk.order_status_update.courier_details_for_return("R2113455")


Update Shipment Status
======================

**Method**

``sdk.order_status_update.update(payload: dict)``

Updates the live tracking status for an order, including:

- In Transit  
- Out for Delivery  
- Delivered  
- RTO  
- Lost  
- Returned  

**Example**

.. code-block:: python

    response = sdk.order_status_update.update(payload)

-------------------------
Environment Variables
-------------------------

``.env`` configuration:

.. code-block:: bash

    ESHOPBOX_WORKSPACE="your-workspace"
    ESHOPBOX_CLIENT_ID="your-client-id"
    ESHOPBOX_SECRET_ID="your-secret-id"
    ESHOPBOX_REFRESH_TOKEN="your-refresh-token"

-------------------------
Next Steps
-------------------------

- See :ref:`orders_api` for order creation.  
- See :ref:`shipments_api` for full shipping workflow.  
- See :ref:`inventory_api` for stock management.

