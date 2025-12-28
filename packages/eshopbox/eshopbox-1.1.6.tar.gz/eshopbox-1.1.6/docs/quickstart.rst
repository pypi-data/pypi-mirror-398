Quickstart
==========

Initialize the SDK:

.. code-block:: python

   from eshopbox import EShopBoxSDK

   sdk = EShopBoxSDK(
       workspace="myshop",
       client_id="CLIENT_ID",
       client_secret="SECRET",
       refresh_token="REFRESH_TOKEN"
   )

Retrieve orders:

.. code-block:: python

   orders = sdk.orders.get_all()
   print(orders)

Create a shipment:

.. code-block:: python

   shipment = sdk.shipments.create({...})
   print(shipment)
