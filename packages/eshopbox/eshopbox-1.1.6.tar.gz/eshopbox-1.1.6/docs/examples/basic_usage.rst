Basic Usage Examples
====================

Initialize SDK:

.. code-block:: python

   from eshopbox import EShopBoxSDK

   sdk = EShopBoxSDK(
       workspace="demo",
       client_id="123",
       client_secret="abc",
       refresh_token="token"
   )

Fetch orders:

.. code-block:: python

   data = sdk.orders.get_all(page=1)
   print(data)

Fetch product info:

.. code-block:: python

   product = sdk.products.get("SKU123")
   print(product)
