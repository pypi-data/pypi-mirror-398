.. _inventory_api:

=====================
Inventory Management
=====================

The EShopBox SDK provides simple methods to **fetch** and **update** inventory
for any SKU in your workspace.

This guide demonstrates how to use:

* ``sdk.inventory.get_stock()`` — Retrieve real-time inventory.
* ``sdk.inventory.update_stock()`` — Update available stock quantities.

Before using the inventory API, ensure you have initialized the SDK with valid
credentials.

------------------------
Basic Usage Example
------------------------

Below is a complete working script showing how to manage inventory using the
EShopBox SDK.

.. code-block:: python

    """
    Example: Manage Inventory using EShopBox SDK
    """

    from eshopbox import EShopBoxSDK
    import os
    from dotenv import load_dotenv
    load_dotenv()

    def main():
        sdk = EShopBoxSDK(
            workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
            client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
            client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
            refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
        )

        sku = "SKU1234"

        print(f"Fetching inventory for {sku}...")
        inventory = sdk.inventory.get_stock(sku)
        print("Current stock:", inventory)

        print(f"Updating inventory for {sku}...")
        update_payload = {
            "sku": sku,
            "quantity": 25
        }

        updated = sdk.inventory.update_stock(update_payload)
        print("Updated stock:", updated)

    if __name__ == "__main__":
        main()

------------------------
API Reference
------------------------

Get Inventory
==============

**Method**

``sdk.inventory.get_stock(sku: str)``

**Description**

Fetch current available inventory for a SKU.

**Example**

.. code-block:: python

    inventory = sdk.inventory.get_stock("SKU1234")
    print(inventory)


Update Inventory
=================

**Method**

``sdk.inventory.update_stock(payload: dict)``

**Description**

Update stock for a specific SKU.

**Payload Example**

.. code-block:: json

    {
        "sku": "SKU1234",
        "quantity": 25
    }

**Example**

.. code-block:: python

    update_payload = {
        "sku": "SKU1234",
        "quantity": 25
    }

    updated = sdk.inventory.update_stock(update_payload)
    print(updated)

------------------------
Environment Variables
------------------------

The SDK reads credentials from environment variables:

.. code-block:: bash

    ESHOPBOX_WORKSPACE="your-workspace"
    ESHOPBOX_CLIENT_ID="your-client-id"
    ESHOPBOX_SECRET_ID="your-secret-id"
    ESHOPBOX_REFRESH_TOKEN="your-refresh-token"

------------------------
Next Steps
------------------------

- See :ref:`orders_api` for creating and managing customer orders.
- See :ref:`products_api` for creating and updating catalog products.

