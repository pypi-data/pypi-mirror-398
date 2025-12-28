"""
Example: Track shipment using EShopBox
"""

from eshopbox import EShopBox
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
    order_status_update = sdk.order_status_update.create_label_and_awb(payload)
    print(order_status_update)


def get_awb_and_courier_name(sdk):
    params = {
        "orderItemIds": "49252941,49252802"
    }
    order_status_update = sdk.order_status_update.get_awb_and_courier_name(params)
    print(order_status_update)


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
    order_status_update = sdk.order_status_update.dispatch_shipment(payload)
    print(order_status_update)


def courier_details_for_return(sdk):
    order_status_update = sdk.order_status_update.courier_details_for_return("R2113455")
    print(order_status_update)


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
    order_status_update = sdk.order_status_update.update(payload)
    print(order_status_update)


def main():
    sdk = EShopBox(
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
