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
