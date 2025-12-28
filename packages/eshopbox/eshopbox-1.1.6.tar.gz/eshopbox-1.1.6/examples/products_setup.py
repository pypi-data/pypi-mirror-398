"""
Example: Setup Products using EShopBox SDK
"""

from eshopbox import EShopBoxSDK
import os
from dotenv import load_dotenv
load_dotenv()


def get_all(sdk):
    params = {
        "fields": "12",
        "ids": "12"
    }
    response = sdk.products.get_all(params)
    print(response)


def get(sdk):
    response = sdk.products.get("kw-12")
    print(response)


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
            "others": [
                "57182_Brown_32"
            ]
        }
    }
    response = sdk.products.create(product_data)
    print(response)


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


def delete(sdk):
    response = sdk.products.delete("73682939-172882-32")
    print(response)


def merge_product(sdk):
    payload = {
        "fromProductESIN": "dgdfgfd",
        "toProductESIN": "sdkdgl"
    }
    response = sdk.products.merge_product(payload)
    print(response)


def product_availability(sdk):
    payload = {
        "esin": "0SGAT12SG25F",
        "channelCode": "CH1234",
        "availability": False
    }
    response = sdk.products.product_availability(payload)
    print(response)


def get_all_brands(sdk):
    response = sdk.products.get_all_brands()
    print(response)


def get_brand(sdk):
    response = sdk.products.get_brand("1429")
    print(response)


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
    response = sdk.products.update_brand('6312', payload)
    print(response)


def get_inventory_for_given_product_v1(sdk):
    payload = {
        "skus": [
            "kw-100"
        ]
    }
    response = sdk.products.get_inventory_for_given_product_v1(payload)
    print(response)


def get_inventory_for_given_product_v2(sdk):
    params = {
        "page": 1
    }
    response = sdk.products.get_inventory_for_given_product_v2(params)
    print(response)


def get_inventory_summary(sdk):
    params = {
        "warehouseId": 1
    }
    response = sdk.products.get_inventory_summary(params)
    print(response)


def main():
    # Initialize SDK
    sdk = EShopBoxSDK(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )
    # get_all(sdk)
    # get(sdk)
    # create(sdk)
    # update(sdk)
    # delete(sdk)
    # merge_product(sdk)
    # product_availability(sdk)
    # get_all_brands(sdk)
    # get_brand(sdk)
    # create_brand(sdk)
    # update_brand(sdk)
    # get_inventory_for_given_product_v1(sdk)
    # get_inventory_for_given_product_v2(sdk)
    get_inventory_summary(sdk)


if __name__ == "__main__":
    main()
