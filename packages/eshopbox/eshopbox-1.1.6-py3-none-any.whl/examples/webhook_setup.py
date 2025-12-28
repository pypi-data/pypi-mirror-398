"""
Example: Setup webhook using EShopBox SDK
"""

import os
from eshopbox.client import EShopBoxSDK
from dotenv import load_dotenv
load_dotenv()


def get_all_webhooks(sdk):
    print("Getting all webhooks...")
    response = sdk.webhooks.list()
    print("Webhooks retrieved successfully!")
    print(response)


def get_webhooks(sdk, id):
    print("Getting specific webhooks...")
    response = sdk.webhooks.get(id)
    print("Webhooks retrieved successfully!")
    print(response)


def create_webhooks(sdk):
    print("Creating webhook...")
    webhook_data = {
        "resource": "user_invitation",
        "eventType": "POST",
        "eventSubType": "created",
        "version": "v1",
        "externalChannelID": os.getenv('ESHOPBOX_EXTERNAL_CHANNEL_ID', ''),
        "webhookUrl": "https://api-dev.kashwork.com/api/shipping/eshopbox/webhook",
        "webhookMethod": "POST",
        "accountSlug": os.getenv('ESHOPBOX_WORKSPACE', '')
    }
    response = sdk.webhooks.create(webhook_data)
    print("Webhook created successfully!")
    print(response)


def update_webhooks(sdk, id):
    print("Updating webhook...")
    webhook_data = {
        "id": id,
        "resource": "channel_inventory",
        "eventType": "POST",
        "eventSubType": "created",
        "version": "v1",
        "externalChannelID": os.getenv('ESHOPBOX_EXTERNAL_CHANNEL_ID', ''),
        "webhookUrl": "https://api-dev.kashwork.com/api/shipping/eshopbox/webhook",
        "webhookMethod": "POST",
        "accountSlug": os.getenv('ESHOPBOX_WORKSPACE', '')
    }
    response = sdk.webhooks.update(webhook_data)
    print("Webhook updated successfully!")
    print(response)


def main():
    sdk = EShopBoxSDK(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )

    # get_all_webhooks(sdk)
    # get_webhooks(sdk, '105322')
    # create_webhooks(sdk)
    update_webhooks(sdk, '105322')


if __name__ == "__main__":
    main()
