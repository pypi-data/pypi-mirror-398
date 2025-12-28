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
