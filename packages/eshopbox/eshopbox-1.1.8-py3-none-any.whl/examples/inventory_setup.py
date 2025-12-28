"""
Example: Manage Inventory using EShopBox
"""

from eshopbox import EShopBox
import os
from dotenv import load_dotenv
load_dotenv()


def main():
    sdk = EShopBox(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )

    sku = "SKU1234"

    print(f"Fetching inventory for {sku}...")
    payload = {
        'skus': []
    }
    inventory = sdk.inventory.get_inventory(payload)
    print("Current stock:", inventory)

    updated = sdk.inventory.get_inventory_summary()
    print("Updated stock:", updated)


if __name__ == "__main__":
    main()
