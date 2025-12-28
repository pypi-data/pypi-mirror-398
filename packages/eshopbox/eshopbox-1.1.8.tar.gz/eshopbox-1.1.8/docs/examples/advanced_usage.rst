Advanced Usage Examples
=======================

Webhook Registration
--------------------

.. code-block:: python

   response = sdk.webhooks.create({
      "resource": "user_invitation",
        "eventType": "POST",
        "eventSubType": "created",
        "version": "v1",
        "externalChannelID": "CH-3565",
        "webhookUrl": "https://api-dev.kashwork.com/api/shipping/eshopbox/webhook",
        "webhookMethod": "POST",
        "accountSlug": "<your-workspace>"
   })

Rate Calculator
---------------

.. code-block:: python

   rate = sdk.rate_calculator.calculate({
       "journeyType": "forward",
        "pickupPincode": "160071",
        "dropPincode": "247342",
        "orderWeight": "500",
        "length": "12",
        "width": "12",
        "height": "33",
        "paymentMethod": "Prepaid",
        "doorstepQc": False
   })

Inventory Updates
-----------------

.. code-block:: python

   inventory = sdk.inventory.update_stock({
       "sku": "SKU001",
       "quantity": 15
   })
