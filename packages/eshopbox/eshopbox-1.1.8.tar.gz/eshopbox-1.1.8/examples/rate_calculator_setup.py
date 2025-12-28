"""
Example: Setup Rate Calculator using EShopBox
"""

import os
from eshopbox.client import EShopBox
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
    sdk = EShopBox(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )
    rate_calculator(sdk)


if __name__ == "__main__":
    main()
