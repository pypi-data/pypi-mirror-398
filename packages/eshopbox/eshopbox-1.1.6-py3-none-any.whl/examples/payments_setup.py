"""
Example: Setup Payment using EShopBox SDK
"""

from eshopbox import EShopBoxSDK
import os
from dotenv import load_dotenv
load_dotenv()


def get_payouts(sdk):
    response = sdk.payments.get_payouts()
    print(response)


def get_payout(sdk):
    params = {
        "neftId": "neftId"
    }
    response = sdk.payments.get_payout(params)
    print(response)


def create_payout(sdk):
    payload = {
        "fundTransferDate": "2018-09-25 05:30:00",
        "fundTransferAmount": 819901.7199999853,
        "transactionId": "lime3",
        "comments": "Limeroad Testing",
        "ledgerGroupId": "limeroad",
        "portalAccountId": 122,
        "reportUrl": "https://cdn.filestackcontent.com/ckdksjkasl676678687as"
    }
    response = sdk.payments.create_payout(payload)
    print(response)


def update_fee(sdk):
    payload = {
        "portalId": 3,
        "feeId": "40",
        "feeName": None,
        "isInclusiveTax": "0",
        "inclusiveTaxPercentage": "63",
        "chargedFee": "cancelled",
        "chargedFeeCases": "",
        "courierReturnedFee": "",
        "courierReturnedPercent": "",
        "customerReturnedFee": "",
        "customerReturnedPercent": "",
        "validityPeriod": "definite",
        "validFrom": "2019-09-09",
        "validTo": "2019-09-11",
        "fee": [
            {
                "eventType": "shipped",
                "eventSubType": "",
                "partialPercentageValue": "",
                "feeCharged": "CHARGED_FEE"
            },
            {
                "eventType": "returned",
                "eventSubType": "courier",
                "partialPercentageValue": "",
                "feeCharged": "REVERSED_FEE"
            },
            {
                "eventType": "returned",
                "eventSubType": "customer",
                "partialPercentageValue": "",
                "feeCharged": "REVERSED_FEE"
            }
        ],
        "feeRules": [
            {
                "details": {
                    "shippingZone": "regional"
                },
                "feeValues": [
                    {
                        "type": "fixed",
                        "value": 2,
                        "applicableOn": "Per Order",
                        "id": 1
                    }
                ]
            }
        ],
        "id": 603,
        "ruleId": "5d7a4867ad0cf20001e527df",
        "forRevision": True
    }
    response = sdk.payments.update_fee(payload)
    print(response)


def create_fee(sdk):
    payload = {
        "portalId": 2,
        "feeId": "1",
        "feeName": "",
        "isInclusiveTax": "0",
        "inclusiveTaxPercentage": "11",
        "chargedFee": "cancelled",
        "chargedFeeCases": "",
        "courierReturnedFee": "",
        "courierReturnedPercent": "",
        "customerReturnedFee": "",
        "customerReturnedPercent": "",
        "fee": [
            {
                "eventType": "cancelled",
                "eventSubType": "",
                "feeCharged": "CHARGED_FEE"
            }
        ],
        "feeRules": [
            {
                "details": {},
                "feeRanges": [
                    {
                        "rangeType": "product selling price",
                        "rangeTypeUnit": "INR",
                        "minRange": 0,
                        "maxRange": 100
                    }
                ],
                "feeValues": [
                    {
                        "type": "fixed",
                        "partitionRangeType": None,
                        "value": 12,
                        "applicableOn": "Per Order",
                        "partitionRange": None
                    }
                ]
            }
        ],
        "validFrom": "2019-09-01T00:00:00.000Z",
        "feePortalId": "145",
        "validityPeriod": "definite",
        "ruleId": "5d7f2b78ad0cf200017cebbb"
    }
    response = sdk.payments.create_fee(payload)
    print(response)


def get_all_fee(sdk):
    response = sdk.payments.get_all_fee()
    print(response)


def get_fee(sdk):
    params = {
        "feeName": "amazon",
    }
    response = sdk.payments.get_fee(params)
    print(response)


def get_all_transaction_rules(sdk):
    response = sdk.payments.get_all_transaction_rules()
    print(response)


def get_transaction_rule(sdk):
    params = {
        "channelId": 12,
    }
    response = sdk.payments.get_transaction_rule(params)
    print(response)


def create_transaction_rule(sdk):
    payload = {
        "ruleName": "TR2",
        "channelId": "12",
        "feeId": [
            "1",
            "3",
            "5"
        ],
        "dueDays": "7",
        "settlementType": "weekly",
        "settlementDates": "",
        "settlementWeekdays": "Thursday",
        "transactionRuleId": "",
        "status": "",
        "portalId": 2,
        "transactionId": 3
    }
    response = sdk.payments.create_transaction_rule(payload)
    print(response)


def update_transaction_rule(sdk):
    payload = {
        "channelId": "262",
        "feeId": [
            "33"
        ],
        "dueDays": "4",
        "settlementType": "weekly",
        "settlementDates": "2",
        "settlementWeekdays": "Monday,Tuesday",
        "transactionRuleId": "47",
        "status": True,
        "ruleName": "abcd",
        "transactionId": 3
    }
    response = sdk.payments.update_transaction_rule(payload)
    print(response)


def main():
    # Initialize SDK
    sdk = EShopBoxSDK(
        workspace=os.getenv('ESHOPBOX_WORKSPACE', ''),
        client_id=os.getenv('ESHOPBOX_CLIENT_ID', ''),
        client_secret=os.getenv('ESHOPBOX_SECRET_ID', ''),
        refresh_token=os.getenv('ESHOPBOX_REFRESH_TOKEN', '')
    )
    # get_payouts(sdk)
    # get_payout(sdk)
    # create_payout(sdk)
    # update_fee(sdk)
    # create_fee(sdk)
    # get_all_fee(sdk)
    # get_fee(sdk)
    # get_all_transaction_rules(sdk)
    get_transaction_rule(sdk)
    # create_transaction_rule(sdk)
    # update_transaction_rule(sdk)


if __name__ == "__main__":
    main()
