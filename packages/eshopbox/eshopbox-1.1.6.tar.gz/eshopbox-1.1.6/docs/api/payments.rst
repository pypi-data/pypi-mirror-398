Payments
========

This page shows how to use the ``payments`` module of the EShopBox Python SDK
to manage payouts, fees, and transaction rules.

.. contents::
   :local:
   :depth: 2


Initialize SDK
--------------

Before calling any API, initialize the SDK::

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


Get All Payouts
---------------

Example::

    def get_payouts(sdk):
        response = sdk.payments.get_payouts()
        print(response)


Get Single Payout
-----------------

Example::

    def get_payout(sdk):
        params = {
            "neftId": "neftId"
        }
        response = sdk.payments.get_payout(params)
        print(response)


Create Payout
-------------

Example::

    def create_payout(sdk):
        payload = {
            "fundTransferDate": "2018-09-25 05:30:00",
            "fundTransferAmount": 819901.71,
            "transactionId": "lime3",
            "comments": "Limeroad Testing",
            "ledgerGroupId": "limeroad",
            "portalAccountId": 122,
            "reportUrl": "https://cdn.filestackcontent.com/ckdksjkasl676678687as"
        }
        response = sdk.payments.create_payout(payload)
        print(response)


Update Fee
----------

Example::

    def update_fee(sdk):
        payload = {
            "portalId": 3,
            "feeId": "40",
            "isInclusiveTax": "0",
            "inclusiveTaxPercentage": "63",
            "chargedFee": "cancelled",
            "validityPeriod": "definite",
            "validFrom": "2019-09-09",
            "validTo": "2019-09-11",
            "fee": [
                {
                    "eventType": "shipped",
                    "feeCharged": "CHARGED_FEE"
                },
                {
                    "eventType": "returned",
                    "eventSubType": "courier",
                    "feeCharged": "REVERSED_FEE"
                },
                {
                    "eventType": "returned",
                    "eventSubType": "customer",
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


Create Fee
----------

Example::

    def create_fee(sdk):
        payload = {
            "portalId": 2,
            "feeId": "1",
            "isInclusiveTax": "0",
            "inclusiveTaxPercentage": "11",
            "chargedFee": "cancelled",
            "fee": [
                {
                    "eventType": "cancelled",
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
                            "value": 12,
                            "applicableOn": "Per Order"
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


Get All Fees
------------

Example::

    def get_all_fee(sdk):
        response = sdk.payments.get_all_fee()
        print(response)


Get Fee by Name
---------------

Example::

    def get_fee(sdk):
        params = {
            "feeName": "amazon",
        }
        response = sdk.payments.get_fee(params)
        print(response)


Get All Transaction Rules
-------------------------

Example::

    def get_all_transaction_rules(sdk):
        response = sdk.payments.get_all_transaction_rules()
        print(response)


Get a Transaction Rule
----------------------

Example::

    def get_transaction_rule(sdk):
        params = {
            "channelId": 12,
        }
        response = sdk.payments.get_transaction_rule(params)
        print(response)


Create Transaction Rule
-----------------------

Example::

    def create_transaction_rule(sdk):
        payload = {
            "ruleName": "TR2",
            "channelId": "12",
            "feeId": ["1", "3", "5"],
            "dueDays": "7",
            "settlementType": "weekly",
            "settlementWeekdays": "Thursday",
            "portalId": 2,
            "transactionId": 3
        }
        response = sdk.payments.create_transaction_rule(payload)
        print(response)


Update Transaction Rule
-----------------------

Example::

    def update_transaction_rule(sdk):
        payload = {
            "channelId": "262",
            "feeId": ["33"],
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
