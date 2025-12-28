"""
Example: Setup Wrapper using EShopBox SDK
"""

from eshopbox import EShopBox
import os
from dotenv import load_dotenv
load_dotenv()


def order(sdk):
    payload = {
        "channelId": os.getenv('ESHOPBOX_EXTERNAL_CHANNEL_ID'),
        "customerOrderId": "OD119208447831346001",
        "shipmentId": "OD119208447831346001-4380-3659",
        "orderDate": "2024-01-01 09:00:00",
        "isCOD": True,
        "invoiceTotal": 4049.09,
        "shippingMode": "Eshopbox Standard",
        "invoice": {
            "number": "C00011323A000002",
            "date": "2024-01-04 09:00:00"
        },
        "ewaybillNumber": "123422267332",
        "balanceDue": 0,
        "shippingAddress": {
            "customerName": "Sakib Malik",
            "addressLine1": "D151",
            "addressLine2": "industrail Area",
            "city": "Mohali",
            "state": "Punjab",
            "postalCode": "160071",
            "countryCode": "IN",
            "country": "India",
            "contactPhone": "xxxxxxxxxx",
            "email": "xxxxxxxxxxxxxxx@gmail.com",
            "gstin": "344633257673"
        },
        "billingIsShipping": True,
        "billingAddress": {
            "customerName": "Sakib Malik",
            "addressLine1": "D151",
            "addressLine2": "industrail Area",
            "city": "Mohali",
            "state": "Punjab",
            "postalCode": "160071",
            "countryCode": "IN",
            "countryName": "India",
            "contactPhone": "xxxxxxxxxx",
            "email": "xxxxxxxxxxxxxxx@gmail.com"
        },
        "items": [
            {
                "id": 49252941,
                "lineItemSequenceNumber": 100,
                "orderItemID": "OD119208447831346001-49252941",
                "itemID": "KW-100",
                "sku": "23YCU3I7KIF",
                "productName": "Keyboard",
                "quantity": 1,
                "customerPrice": 4499,
                "discount": 449.89,
                "lineItemTotal": 4049.09,
                "taxRate": 12,
                "taxAmount": 0,
                "giftMessage": "",
                "giftLabelContent": "",
                "cancellationReason": "",
                "cancellationTime": "0000-00-00 00:00:00",
                "original_order_item_id": None,
                "isVirtualKit": "0",
                "productAdditionalInfo": {
                    "size": None,
                    "color": None,
                    "weight": 20.99,
                    "height": 12.13,
                    "length": 11.13,
                    "width": 8.13,
                    "taxPercentage": 12,
                    "hsnCode": "HSN1324",
                    "productDetails": {
                        "hsnCode": "HSN1324",
                        "dimensionHeight": 12.13,
                        "dimensionLength": 11.13,
                        "description": "Keyboard",
                        "weight": 20.99,
                        "mrp": 6000,
                        "dimensionWidth": 8.13,
                        "type": "BASE",
                        "taxCode": "ESBGST9",
                        "imageUrl": "https://kw-live.s3.amazonaws.com/media/post_images/upload/product_pic_d4bda7fb-e2f1-4061-b2ef-e4a5bd7618b8.webp",
                        "accountSlug": "kashwork-ecommerce",
                        "sku": "KW-123",
                        "esin": "23YCU3I7KIF",
                        "status": "DRAFT",
                        "weightUnit": "g"
                    }
                },
                "productImageUrl": "https://kw-live.s3.amazonaws.com/media/post_images/upload/product_pic_d4bda7fb-e2f1-4061-b2ef-e4a5bd7618b8.webp",
                "productUrl": "https://kashwork.com/d/jewellery/imitation_jewellery/women_imitation_jewellery_/women_necklace_sets/dabka_jewellery_set/161291130/598744146",
                "invoiceTotal": 4049.09,
                "shippingCharges": 0,
                "giftWrapCharges": 0,
                "cashOnDeliveryCharges": 0
            }
        ],
        "shipmentDimension": {
            "length": 13.12,
            "breadth": 15.32,
            "height": 56.39,
            "weight": 201.23
        },
        "pickupLocation": {
            "locationCode": "MCFL00395",
            "locationName": "TEST Warehouse",
            "companyName": "TEST",
            "contactPerson": "SAM",
            "contactNumber": "898898989",
            "addressLine1": "Khasra no 5/16/2,17, Near Subash Chowk, Sohana Road Village Behrampur",
            "addressLine2": "Khasra no 5/16/2,17, Near Subash Chowk",
            "city": "Gurgaon",
            "state": "HARYANA",
            "country": "India",
            "pincode": "121005",
            "gstin": "06AAFCM7888Q1ZE"
        },
        "package": {
            "type": "box",
            "code": "PC20240613141533",
            "description": "Test1",
            "length": 45.00,
            "breadth": 54.13,
            "height": 45.22,
            "weight": 45.80
        }
    }
    response = sdk.wrapper.order(payload)
    print("Response: ", response)


def shipping_return(sdk):
    payload = {
        "channelId": "KAPAS KRAFT",
        "customerOrderId": "OD119208447831346000",
        "shipmentId": "2313ewqwre",
        "orderDate": "2020-02-29 15:39:11",
        "isCOD": True,
        "invoiceTotal": 4049.09,
        "shippingMode": "Standard",
        "invoice": {
            "number": "C00011323A000002",
            "date": "2023-06-02 15:39:11"
        },
        "ewaybillNumber": "",
        "shippingAddress": {
            "locationCode": "MCFL00395",
            "locationName": "TEST Warehouse",
            "companyName": "TEST",
            "contactPerson": "SAM",
            "contactNumber": "898898989",
            "addressLine1": "Khasra no 5/16/2,17, Near Subash Chowk, Sohana Road Village Behrampur",
            "addressLine2": "Khasra no 5/16/2,17, Near Subash Chowk",
            "city": "Gurgaon",
            "pincode": "121005",
            "state": "HARYANA",
            "country": "India",
            "gstin": "06AAFCM7888Q1ZE"
        },
        "items": [
            {
                "itemID": "DB9U03FMGWZ",
                "productTitle": "Pace Barnes",
                "quantity": 1,
                "itemTotal": 4049.09,
                "hsn": "122132",
                "mrp": 2345.98,
                "discount": 123,
                "taxPercentage": 12.00,
                "returnReason": "TEST",
                "ean": "2342534",
                "length": 12,
                "breadth": 18,
                "height": 23,
                "weight": 100,
                "qcDetails": {
                    "qc_color": "red",
                    "qc_brand": "duke",
                    "qc_serial_no": "212324235",
                    "qc_ean_barcode": "sdsrewrt",
                    "qc_size": "22",
                    "qc_product_name": "TEST",
                    "qc_product_image": "IMG.png",
                    "qcParamsToCheck": [
                        "check_price_tag",
                        "check_packaging_box",
                        "check_damaged",
                        "check_used"
                    ]
                }
            }
        ],
        "returnDimension": {
            "length": 13.12,
            "breadth": 15.32,
            "height": 56.39,
            "weight": 201.23
        },
        "pickupLocation": {
            "customerName": "John Doe",
            "addressLine1": "Kapas Kraft Apparels Limited",
            "addressLine2": "Banglore",
            "city": "bengluru",
            "state": "Karnataka",
            "pincode": "560005",
            "country": "India",
            "contactPhone": "9998889998",
            "email": "johndoe@gmail.com"
        }
    }
    response = sdk.wrapper.shipping_return(payload)
    print("Response: ", response)


def cancel_tracking(sdk):
    payload = {
        "trackingId": "1231244"
    }
    response = sdk.wrapper.cancel_tracking(payload)
    print("Response: ", response)


def tracking_details(sdk):    
    response = sdk.wrapper.tracking_details("OD119208447831346000-4380-3659")
    print("Response: ", response)


def webhook_register(sdk):
    payload = {
        "resource": "channel_inventory",
        "eventType": "POST",
        "eventSubType": "updated",
        "version": "v1",
        "externalChannelID": "TEST",
        "webhookUrl": "https://webhook.testurl.com/fake-subscription-url2",
        "webhookMethod": "POST",
        "webhookHeaders": {
            "x-api-key": "test1234",
            "sample-header-key": "test875876",
            "authorization": "Bearer abcdef123456",
            "custom-header": "customValue",
            "content-type": "application/json"
        }
    }

    response = sdk.wrapper.webhook_register(payload, ProxyHost="your_proxy_host_value")
    print("Response: ", response)


def main():
    # Initialize SDK
    sdk = EShopBox(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )
    # order(sdk)
    # shipping_return(sdk)
    # cancel_tracking(sdk)
    # tracking_details(sdk)
    webhook_register(sdk)


if __name__ == "__main__":
    main()
