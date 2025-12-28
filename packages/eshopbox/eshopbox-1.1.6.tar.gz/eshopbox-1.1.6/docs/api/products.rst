Products
========

This page provides examples on how to use the **Products** module of the
``EShopBoxSDK`` to manage products, brands, and inventory.

Basic Setup
-----------

Before running any operation, initialize the SDK:

.. code-block:: python

    from eshopbox import EShopBoxSDK
    import os
    from dotenv import load_dotenv
    load_dotenv()

    sdk = EShopBoxSDK(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )

Get All Products
----------------

.. code-block:: python

    def get_all(sdk):
        params = {
            "fields": "12",
            "ids": "12"
        }
        response = sdk.products.get_all(params)
        print(response)

Get a Single Product
--------------------

.. code-block:: python

    def get(sdk):
        response = sdk.products.get("kw-12")
        print(response)

Create a Product
----------------

.. code-block:: python

    def create(sdk):
        product_data = {
            "type": "BASE",
            "sku": "73682939-172882-32",
            "groupCode": "73682939-172882",
            "vertical": "APL",
            "brand": "Kapas Kraft",
            "description": "Rust Regular Fit Bundi",
            "specification": [
                "Fragile",
                "Dangerous",
                "Liquid"
            ],
            "additionalNames": {
                "ean": "89027189271829",
                "upc": "87162143127",
                "gtin": "8276174829301",
                "others": ["57182_Brown_32"]
            }
        }
        response = sdk.products.create(product_data)
        print(response)

Update a Product
----------------

.. code-block:: python

    def update(sdk):
        product_data = {
            "imageUrl": "https://cdn.filestackcontent.com/hdYluVCqSADCASjjjcuaeC.png",
            "mrp": 1499.0,
            "unitPrice": 799.0,
            "hsnCode": "6101112",
            "weight": 167.0,
            "dimensionLength": 5.0,
            "dimensionWidth": 5.0,
            "dimensionHeight": 5.0,
            "dimensionUnit": "cm"
        }
        response = sdk.products.update("73682939-172882-32", product_data)
        print(response)

Delete a Product
----------------

.. code-block:: python

    def delete(sdk):
        response = sdk.products.delete("73682939-172882-32")
        print(response)

Merge Products
--------------

.. code-block:: python

    def merge_product(sdk):
        payload = {
            "fromProductESIN": "dgdfgfd",
            "toProductESIN": "sdkdgl"
        }
        response = sdk.products.merge_product(payload)
        print(response)

Product Availability
--------------------

.. code-block:: python

    def product_availability(sdk):
        payload = {
            "esin": "0SGAT12SG25F",
            "channelCode": "CH1234",
            "availability": False
        }
        response = sdk.products.product_availability(payload)
        print(response)

Brand Management
================

Get All Brands
--------------

.. code-block:: python

    def get_all_brands(sdk):
        response = sdk.products.get_all_brands()
        print(response)

Get a Brand
-----------

.. code-block:: python

    def get_brand(sdk):
        response = sdk.products.get_brand("1429")
        print(response)

Create a Brand
--------------

.. code-block:: python

    def create_brand(sdk):
        payload = {
            "brandName": "SAKIB",
            "verticals": [
                {
                    "verticalId": "1",
                    "verticalName": "apparels",
                    "verticalCode": "apl",
                    "mainImage": "abc.jpg",
                    "hoverImage": "abc.jpg"
                },
                {
                    "verticalId": "2",
                    "verticalName": "footwear",
                    "verticalCode": "ftq",
                    "mainImage": "abc.jpg",
                    "hoverImage": "abc.jpg"
                }
            ],
            "accountId": "123",
            "brandCode": "ABC123",
            "brandStatus": "1",
            "webSiteLink": "http://Kapas Kraft",
            "brandLogoImage": "Kpas Kraft logo.jpg",
            "tmRegistrationStatus": "abc",
            "tmCertificateScannedCopy": "URL",
            "tAckNo": "1",
            "tmRegistrationNo": "123",
            "tmRegistrationDate": "2019-03-20 00:00:00",
            "tmAckCert": "URL"
        }
        response = sdk.products.create_brand(payload)
        print(response)

Update a Brand
--------------

.. code-block:: python

    def update_brand(sdk):
        payload = {
            "brandName": "SAKIB",
            "verticals": [
                {
                    "verticalId": "1",
                    "verticalName": "apparels",
                    "verticalCode": "apl",
                    "mainImage": "abc.jpg",
                    "hoverImage": "abc.jpg"
                },
                {
                    "verticalId": "2",
                    "verticalName": "footwear",
                    "verticalCode": "ftq",
                    "mainImage": "abc.jpg",
                    "hoverImage": "abc.jpg"
                }
            ],
            "accountId": "XXX",
            "brandCode": "ABC123",
            "brandStatus": "1",
            "webSiteLink": "XXXXXXXXXXXX Kraft",
            "brandLogoImage": "Kpas Kraft logo.jpg",
            "tmRegistrationStatus": "abc",
            "tmCertificateScannedCopy": "URL",
            "tAckNo": "1",
            "tmRegistrationNo": "123",
            "tmRegistrationDate": "2019-03-20 00:00:00",
            "tmAckCert": "URL"
        }
        response = sdk.products.update_brand("6312", payload)
        print(response)


Inventory APIs
==============

Inventory for Given Product (V1)
--------------------------------

.. code-block:: python

    def get_inventory_for_given_product_v1(sdk):
        payload = {"skus": ["kw-100"]}
        response = sdk.products.get_inventory_for_given_product_v1(payload)
        print(response)

Inventory for Given Product (V2)
--------------------------------

.. code-block:: python

    def get_inventory_for_given_product_v2(sdk):
        params = {"page": 1}
        response = sdk.products.get_inventory_for_given_product_v2(params)
        print(response)

Inventory Summary
-----------------

.. code-block:: python

    def get_inventory_summary(sdk):
        params = {"warehouseId": 1}
        response = sdk.products.get_inventory_summary(params)
        print(response)

Running the Example
-------------------

.. code-block:: python

    if __name__ == "__main__":
        main()

