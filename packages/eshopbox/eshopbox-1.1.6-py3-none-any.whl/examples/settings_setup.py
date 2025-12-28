"""
Example: Setup Settings using EShopBox SDK
"""

from eshopbox import EShopBoxSDK
import os
from dotenv import load_dotenv
load_dotenv()


def get_portals(sdk):
    response = sdk.settings.get_portals()
    print(response)


def create_workspace(sdk):
    data = {
        "data": {
            "accountSlug": "eshop",
            "accountName": "Eshopbox"
        }
    }
    response = sdk.settings.create_workspace(data)
    print(response)


def get_all_workspace(sdk):
    params = {
        "page": 1,
        "limit": 10
    }
    response = sdk.settings.get_all_workspace(params)
    print(response)


def get_workspace(sdk):
    response = sdk.settings.get_workspace()
    print(response)


def update_workspace(sdk):
    data = {
        "data": {
            "accountSlug": "eshop",
            "accountName": "XXXXXXXX"
        }
    }
    response = sdk.settings.update_workspace(data)
    print(response)


def create_sales_channel(sdk):
    data = {
        "data": {
            "portalId": 1,
            "integrationModelId": 1,
            "channelAccountId": 1,
            "fulfillmentChannels": [
                {
                    "warehouseId": 1
                },
                {
                    "warehouseId": 2
                }
            ]
        }
    }
    response = sdk.settings.create_sales_channel(data)
    print(response)


def update_sales_channel(sdk):
    data = {
        "data": {
            "portalId": 1,
            "integrationModelId": 1,
            "channelAccountId": 1,
            "fulfillmentChannels": [
                {
                    "warehouseId": 1
                },
                {
                    "warehouseId": 2
                }
            ]
        }
    }
    response = sdk.settings.update_sales_channel(1, data)
    print(response)


def get_all_sales_channel(sdk):
    response = sdk.settings.get_all_sales_channel()
    print(response)


def get_sales_channel(sdk):
    response = sdk.settings.get_sales_channel(4801)
    print(response)


def create_fc_submission(sdk):
    data = {
        "data": {
            "warehouseId": "1",
            "warehouseName": "TCNS Banglore",
            "externalWmsAccountId": "1",
            "facility": "BDBLR108",
            "operatingModel": "consignment",
            "requestDocuments": {
                "gstCertificateUrl": "http://abc.com/1.jpg",
                "signatureUrl": "http://abc.com/2.jpg",
                "companyLogoUrl": "http://abc.com/3.jpg"
            }
        }
    }
    response = sdk.settings.create_fc_submission(data)
    print(response)


def get_all_fc_submission(sdk):
    response = sdk.settings.get_all_fc_submission()
    print(response)


def get_fc_submission(sdk):
    response = sdk.settings.get_fc_submission(1)
    print(response)


def create_contact(sdk):
    data = {
        "data": {
            "contactCode": "1234",
            "contactName": "ABC",
            "contactEmail": "XXXXXXXXXXXXX",
            "contactPhone": "1234567890",
            "contactType": "seller",
            "contactAddress": "ABC"
        }
    }
    response = sdk.settings.create_contact(data)
    print(response)


def update_fc_submission(sdk):
    data = {
        "data": {
            "warehouseId": "1",
            "warehouseName": "TCNS Banglore",
            "externalWmsAccountId": "1",
            "facility": "BDBLR108",
            "operatingModel": "consignment",
            "requestDocuments": {
                "gstCertificateUrl": "XXXXXXXXXXXXXXXXXXXX",
                "signatureUrl": "XXXXXXXXXXXXXXXXXXXX",
                "companyLogoUrl": "XXXXXXXXXXXXXXXXXXXX"
            }
        }
    }
    response = sdk.settings.update_fc_submission(1, data)
    print(response)


def get_all_contact(sdk):
    response = sdk.settings.get_all_contact()
    print(response)


def get_contact(sdk):
    params = {
        "contactCode": "1234"
    }
    response = sdk.settings.get_contact(params)
    print(response)


def update_contact(sdk):
    data = {
        "data": {
            "contactCode": "1234",
            "contactName": "ABC",
            "contactEmail": "XXXXXXXXXXXXX",
            "contactPhone": "1234567890",
            "contactType": "seller",
            "contactAddress": "ABC"
        }
    }
    response = sdk.settings.update_contact("1234", data)
    print(response)


def create_team_member(sdk):
    data = {
        "data": {
            "userId": 1,
            "portalId": 1,
            "integrationModelId": 1,
            "channelAccountId": 1,
            "warehouseId": 1
        }
    }
    response = sdk.settings.create_team_member(data)
    print(response)


def update_team_member(sdk):
    data = {
        "data": {
            "userId": 1,
            "portalId": 1,
            "integrationModelId": 1,
            "channelAccountId": 1,
            "warehouseId": 1
        }
    }
    response = sdk.settings.update_team_member(1, data)
    print(response)


def get_team_member(sdk):
    response = sdk.settings.get_team_member(1)
    print(response)


def get_all_team_member(sdk):
    response = sdk.settings.get_all_team_member()
    print(response)


def main():
    # Initialize SDK
    sdk = EShopBoxSDK(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )

    # get_portals(sdk)
    # create_workspace(sdk)
    # get_all_workspace(sdk)
    # get_workspace(sdk)
    # update_workspace(sdk)
    # create_sales_channel(sdk)
    # update_sales_channel(sdk)
    # get_all_sales_channel(sdk)
    # get_sales_channel(sdk)
    # create_fc_submission(sdk)
    # get_all_fc_submission(sdk)
    # get_fc_submission(sdk)
    # update_fc_submission(sdk)
    # create_contact(sdk)
    # get_all_contact(sdk)
    # get_contact(sdk)
    # update_contact(sdk)
    # create_team_member(sdk)
    # update_team_member(sdk)
    # get_team_member(sdk)
    get_all_team_member(sdk)


if __name__ == "__main__":
    main()
