Webhooks
========

The **Webhooks** module in the EShopBox SDK allows you to manage webhook subscriptions for workspace events.  
You can list, create, update, and retrieve webhooks programmatically.

Example: Setup Webhook Using EShopBox SDK
-----------------------------------------

.. code-block:: python

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

        update_webhooks(sdk, '105322')


    if __name__ == "__main__":
        main()


Webhook APIs
------------

List All Webhooks
~~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.webhooks.list()

Returns a list of all webhooks for the workspace.


Get a Specific Webhook
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.webhooks.get(webhook_id)

Retrieves the details of a specific webhook using its ID.

Example:

.. code-block:: python

    sdk.webhooks.get('105322')


Create a Webhook
~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.webhooks.create(webhook_data)

Creates a new webhook subscription.

**Required Fields in `webhook_data`:**

+-------------------+---------+----------+---------------------------------------------+
| Field             | Type    | Required | Description                                 |
+===================+=========+==========+=============================================+
| resource          | string  | Yes      | Event resource to subscribe to              |
+-------------------+---------+----------+---------------------------------------------+
| eventType         | string  | Yes      | HTTP method type (`POST`, `PUT`, etc.)      |
+-------------------+---------+----------+---------------------------------------------+
| eventSubType      | string  | Yes      | Subtype of event (`created`, `updated`)    |
+-------------------+---------+----------+---------------------------------------------+
| version           | string  | Yes      | API version (`v1`)                           |
+-------------------+---------+----------+---------------------------------------------+
| externalChannelID | string  | Optional | External channel identifier                 |
+-------------------+---------+----------+---------------------------------------------+
| webhookUrl        | string  | Yes      | URL to receive webhook notifications        |
+-------------------+---------+----------+---------------------------------------------+
| webhookMethod     | string  | Yes      | HTTP method used for webhook (`POST`)       |
+-------------------+---------+----------+---------------------------------------------+
| accountSlug       | string  | Yes      | Workspace account slug                       |
+-------------------+---------+----------+---------------------------------------------+


Update a Webhook
~~~~~~~~~~~~~~~~

.. code-block:: python

    sdk.webhooks.update(webhook_data)

Updates an existing webhook by ID.

**Fields for update:** Same as create, but include `id` of the webhook to update.


Notes
-----

- Make sure the webhook URL is publicly accessible and can accept POST requests.  
- Use `externalChannelID` if the webhook is specific to a channel.  
- Webhook creation and update require valid workspace credentials stored in environment variables.
- Event types and resources must match EShopBox webhook specifications.

