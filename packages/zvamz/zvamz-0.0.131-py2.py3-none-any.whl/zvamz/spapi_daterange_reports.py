import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import time
from .ratelimit import RateLimiter
from .fcmap import fc_to_country
from .marketplaces import marketplaces
import gzip
import shutil
from .gmail_automation import gchat_space
import urllib.parse
import time

def _get_report_document_id(report_id, regionUrl, headers):
    """
    This will pull the report document id for the given report id.

    Parameter:
    - report_id: the id of the report to check
    - regionUrl: the url of the region
    - headers: the headers for the request

    return:
    - the document id of the report
    """
    endpoint = f'/reports/2021-06-30/reports/{report_id}'
    url = regionUrl + endpoint
    start_time = time.time()
    timeout_seconds = 3600  # 1 hour

    while True:
        # Check for timeout
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError("Report processing timed out after 1 hour.")

        status_response = requests.get(url, headers=headers)
        if status_response.status_code != 200:
            print(f"Failed to get report status: {status_response.text}")
            time.sleep(60)
            continue
        
        status = status_response.json().get("processingStatus")
        
        if status == "DONE":
            print("Report is ready for download!")
            return status_response.json()["reportDocumentId"]
        elif status in ("CANCELLED", "FATAL"):
            raise ValueError(f"Report generation failed with status: {status}")
        else:
            print(f"Report status: {status}. Waiting for report to be ready...")
            time.sleep(60)  # Wait before checking again

def shipmentEvents_daterange(marketplace_action, access_token, start_date, end_date):
    """
    This will pull Shipment Event Reports per region in a specific date range.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - start_date: start date in ISO format, this is inclusive
    - end_date: end date in ISO format, this is inclusive

    return:
    - data frame of Shipment Event Report
    """
    # Pull API Data
    rate_limiter = RateLimiter(tokens_per_second=0.5, capacity=30)
    records = []
    regionUrl, marketplace_id = marketplace_action()
    NextToken = None

    headers = {
            'x-amz-access-token': access_token
        }

    request_params  = {
        'PostedAfter': start_date,
        'PostedBefore': end_date
    }

    try:
        url = regionUrl + f'/finances/v0/financialEvents' + '?' + urllib.parse.urlencode(request_params)
        response = requests.get(url, headers=headers)
        records.extend(response.json()['payload']['FinancialEvents']['ShipmentEventList'])

        try:
            NextToken = response.json()['payload']['NextToken']
        except:
            NextToken = None

        while NextToken:
            request_params_next  = {
                'NextToken': NextToken
            }
            url = regionUrl + f'/finances/v0/financialEvents' + '?' + urllib.parse.urlencode(request_params_next)
            response = rate_limiter.send_request(requests.get, url, headers=headers)
            records.extend(response.json()['payload']['FinancialEvents']['ShipmentEventList'])

            try:
                NextToken = response.json()['payload']['NextToken']
            except:
                NextToken = None
            
        print('End of List')

    except Exception as e:
        print(f'{response.status_code} - {response.text}')

    # set Data Frame
    taxDf = []
    for record in records:
        data ={
            'amazon_order_id': record.get('AmazonOrderId', np.nan),
            'posted_date': record.get('PostedDate', np.nan),
            'marketplace': record.get('MarketplaceName', np.nan),
            'sku': record.get('ShipmentItemList', [{}])[0].get('SellerSKU', np.nan),
            'qty': record.get('ShipmentItemList', [{}])[0].get('QuantityShipped', np.nan),
            'currency': record.get('ShipmentItemList', [{}])[0].get('ItemChargeList', [{}])[0].get('ChargeAmount',{}).get('CurrencyCode', np.nan),
        }

        charges = record.get('ShipmentItemList', [{}])[0].get('ItemChargeList', [])
        for charge in charges:
            data[charge.get('ChargeType')] = charge.get('ChargeAmount', {}).get('CurrencyAmount', np.nan)

        fees = record.get('ShipmentItemList', [{}])[0].get('ItemFeeList', [])
        for fee in fees:
            data[fee.get('FeeType')] = fee.get('FeeAmount', {}).get('CurrencyAmount', np.nan)

        withhelds = record.get('ShipmentItemList', [{}])[0].get('ItemTaxWithheldList', [{}])[0].get('TaxesWithheld',[])
        for withheld in withhelds:
            data[withheld.get('ChargeType')] = withheld.get('ChargeAmount', {}).get('CurrencyAmount', np.nan)

        taxDf.append(data)

    taxDf = pd.DataFrame(taxDf)

    taxDf['posted_date'] = pd.to_datetime(taxDf['posted_date'])

    req_columns = [
        'amazon_order_id',
        'posted_date',
        'marketplace',
        'sku',
        'qty',
        'currency',
        'Principal',
        'Tax',
        'GiftWrap',
        'GiftWrapTax',
        'ShippingCharge',
        'ShippingTax',
        'FBAPerUnitFulfillmentFee',
        'Commission',
        'FixedClosingFee',
        'GiftwrapChargeback',
        'SalesTaxCollectionFee',
        'ShippingChargeback',
        'VariableClosingFee',
        'DigitalServicesFee',
        'FBAPerOrderFulfillmentFee',
        'FBAWeightBasedFee',
        'MarketplaceFacilitatorTax-Principal',
        'MarketplaceFacilitatorTax-Shipping',
        'MarketplaceFacilitatorVAT-Principal',
        'LowValueGoodsTax-Shipping',
        'LowValueGoodsTax-Principal',
        'MarketplaceFacilitatorVAT-Shipping',
        'MarketplaceFacilitatorTax-Other',
        'RenewedProgramFee'
    ]

    for col in req_columns:
        if col not in taxDf.columns:
            taxDf[col] = np.nan

    taxDf = taxDf[req_columns]

    schema = {
        'amazon_order_id': str,
        'posted_date': 'datetime64[ns, UTC]',
        'marketplace': str,
        'sku': str,
        'qty': float,
        'currency': str,
        'Principal': float,
        'Tax': float,
        'GiftWrap': float,
        'GiftWrapTax': float,
        'ShippingCharge': float,
        'ShippingTax': float,
        'FBAPerUnitFulfillmentFee': float,
        'Commission': float,
        'FixedClosingFee': float,
        'GiftwrapChargeback': float,
        'SalesTaxCollectionFee': float,
        'ShippingChargeback': float,
        'VariableClosingFee': float,
        'DigitalServicesFee': float,
        'FBAPerOrderFulfillmentFee': float,
        'FBAWeightBasedFee': float,
        'MarketplaceFacilitatorTax-Principal': float,
        'MarketplaceFacilitatorTax-Shipping': float,
        'MarketplaceFacilitatorVAT-Principal': float,
        'LowValueGoodsTax-Shipping': float,
        'LowValueGoodsTax-Principal': float,
        'MarketplaceFacilitatorVAT-Shipping': float,
        'MarketplaceFacilitatorTax-Other': float,
        'RenewedProgramFee': float
    }

    taxDf = taxDf.astype(schema)

    return taxDf

def refunds_daterange(marketplace_action, access_token, start_date, end_date):
    """
    This will pull Refund Reports per region in a specific date range.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - start_date: start date in ISO format, this is inclusive
    - end_date: end date in ISO format, this is inclusive

    return:
    - data frame of Refund Report
    """
    # Pull API Data
    rate_limiter = RateLimiter(tokens_per_second=0.5, capacity=30)
    records = []
    regionUrl, marketplace_id = marketplace_action()
    NextToken = None

    headers = {
            'x-amz-access-token': access_token
        }

    request_params  = {
        'PostedAfter': start_date,
        'PostedBefore': end_date
    }

    try:
        url = regionUrl + f'/finances/v0/financialEvents' + '?' + urllib.parse.urlencode(request_params)
        response = requests.get(url, headers=headers)
        records.extend(response.json()['payload']['FinancialEvents']['RefundEventList'])

        try:
            NextToken = response.json()['payload']['NextToken']
        except:
            NextToken = None

        while NextToken:
            request_params_next  = {
                'NextToken': NextToken
            }
            url = regionUrl + f'/finances/v0/financialEvents' + '?' + urllib.parse.urlencode(request_params_next)
            response = rate_limiter.send_request(requests.get, url, headers=headers)
            records.extend(response.json()['payload']['FinancialEvents']['RefundEventList'])

            try:
                NextToken = response.json()['payload']['NextToken']
            except:
                NextToken = None
            
        print('End of List')

    except Exception as e:
        print(f'{response.status_code} - {response.text}')

    # Data Frame
    refunds = []
    for record in records:
        data = {
            'amazon_order_id': record.get('AmazonOrderId', np.nan),
            'seller_order_id': record.get('SellerOrderId', np.nan),
            'marketplace_link': record.get('MarketplaceName', np.nan),
            'refund_date': record.get('PostedDate', np.nan),
            'sku': record.get('ShipmentItemAdjustmentList', [{}])[0].get('SellerSKU', np.nan),
            'order_adjustment_item_id': record.get('ShipmentItemAdjustmentList', [{}])[0].get('OrderAdjustmentItemId', np.nan),
            'quantity': record.get('ShipmentItemAdjustmentList', [{}])[0].get('QuantityShipped', np.nan),
            'currency': record.get('ShipmentItemAdjustmentList', [{}])[0].get('ItemChargeAdjustmentList', [{}])[0].get('ChargeAmount',{}).get('CurrencyCode',np.nan),
        }

        chargeAdjustment = record.get('ShipmentItemAdjustmentList', [{}])[0].get('ItemChargeAdjustmentList', [])
        for charge in chargeAdjustment:
            data['charge_' + charge.get('ChargeType')] = charge.get('ChargeAmount', {}).get('CurrencyAmount', np.nan)

        feeAdjustment = record.get('ShipmentItemAdjustmentList', [{}])[0].get('ItemFeeAdjustmentList', [])
        for fee in feeAdjustment:
            data['fee_' + fee.get('FeeType')] = fee.get('FeeAmount', {}).get('CurrencyAmount', np.nan)

        taxWithheld = record.get('ShipmentItemAdjustmentList', [{}])[0].get('ItemTaxWithheldList', [{}])[0].get('TaxesWithheld',[])
        for tax in taxWithheld:
            data['tax_' + tax.get('ChargeType')] = tax.get('ChargeAmount', {}).get('CurrencyAmount', np.nan)

        refunds.append(data)

    refundsDf = pd.DataFrame(refunds)
    refundsDf = refundsDf.rename(columns=lambda x:x.replace('-','_').lower())

    req_columns = [
        'amazon_order_id',
        'seller_order_id',
        'marketplace_link',
        'refund_date',
        'sku',
        'order_adjustment_item_id',
        'quantity',
        'currency',
        'charge_tax',
        'charge_principal',
        'fee_commission',
        'fee_fixedclosingfee',
        'fee_giftwrapchargeback',
        'fee_refundcommission',
        'fee_shippingchargeback',
        'fee_variableclosingfee',
        'fee_digitalservicesfee',
        'tax_marketplacefacilitatortax_principal',
        'charge_restockingfee',
        'charge_shippingtax',
        'charge_shippingcharge',
        'fee_salestaxcollectionfee',
        'charge_returnshipping',
        'tax_marketplacefacilitatortax_shipping',
        'charge_exportcharge',
        'charge_giftwrap',
        'charge_giftwraptax',
        'tax_marketplacefacilitatorvat_principal',
        'fee_renewedprogramfee',
        'tax_marketplacefacilitatorvat_shipping'
    ]

    for col in req_columns:
        if col not in refundsDf.columns:
            refundsDf[col] = np.nan

    refundsDf = refundsDf[req_columns]

    schema = {
        'amazon_order_id': str,
        'seller_order_id': str,
        'marketplace_link': str,
        'refund_date': 'datetime64[ns, UTC]',
        'sku': str,
        'order_adjustment_item_id': str,
        'quantity': float,
        'currency': str,
        'charge_tax': float,
        'charge_principal': float,
        'fee_commission': float,
        'fee_fixedclosingfee': float,
        'fee_giftwrapchargeback': float,
        'fee_refundcommission': float,
        'fee_shippingchargeback': float,
        'fee_variableclosingfee': float,
        'fee_digitalservicesfee': float,
        'tax_marketplacefacilitatortax_principal': float,
        'charge_restockingfee': float,
        'charge_shippingtax': float,
        'charge_shippingcharge': float,
        'fee_salestaxcollectionfee': float,
        'charge_returnshipping': float,
        'tax_marketplacefacilitatortax_shipping': float,
        'charge_exportcharge': float,
        'charge_giftwrap': float,
        'charge_giftwraptax': float,
        'tax_marketplacefacilitatorvat_principal': float,
        'fee_renewedprogramfee': float,
        'tax_marketplacefacilitatorvat_shipping': float
    }

    refundsDf = refundsDf.astype(schema)

    return refundsDf

def all_orders_daterange(marketplace_action, access_token, start_date, end_date, file_path_name):
    """
    This will pull All Orders Report per region in a specific date range.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - start_date: start date in ISO format, this is inclusive
    - end_date: end date in ISO format, this is inclusive
    - file_path_name: file path up to file name where to save the initially downloaded report

    return:
    - data frame of Refund Report
    """
    # Create Report
    regionUrl , marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL',
        'dataStartTime': start_date,
        'dataEndTime': end_date
    }

    create_response = requests.post(url, headers=headers, json=request_params,)
    report_id = create_response.json()['reportId']

    document_id = _get_report_document_id(report_id, regionUrl, headers)

    # Download Report
    endpoint = f'/reports/2021-06-30/documents/{document_id}'
    url = regionUrl + endpoint
    document_response = requests.get(url, headers=headers)

    if document_response.status_code == 200:
        download_url = document_response.json()["url"]
        compression_algorithm = document_response.json().get("compressionAlgorithm")
        report_data = requests.get(download_url)
        
        if compression_algorithm == "GZIP":
            print('Decompressing...')

            with open(file_path_name + '.gz', 'wb') as f:
                f.write(report_data.content)

            with gzip.open(file_path_name + '.gz', 'rb') as f_in:
                with open(file_path_name, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        else:
            with open(file_path_name, 'wb') as f:
                f.write(report_data.content)

        print('Report Downloaded!')

    else:
        print("Failed to get the report document:", document_response.json())

    # Process DF
    allOrdersDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    allOrdersDf = allOrdersDf.rename(columns=lambda x:x.replace('-','_').replace(' ','_').lower())
    allOrdersDf['purchase_date'] = pd.to_datetime(allOrdersDf['purchase_date'])
    allOrdersDf['last_updated_date'] = pd.to_datetime(allOrdersDf['last_updated_date'])

    req_columns = [
        'amazon_order_id',
        'merchant_order_id',
        'purchase_date',
        'last_updated_date',
        'order_status',
        'fulfillment_channel',
        'sales_channel',
        'order_channel',
        'ship_service_level',
        'product_name',
        'sku',
        'asin',
        'number_of_items',
        'item_status',
        'tax_collection_model',
        'tax_collection_responsible_party',
        'quantity',
        'currency',
        'item_price',
        'item_tax',
        'shipping_price',
        'shipping_tax',
        'gift_wrap_price',
        'gift_wrap_tax',
        'item_promotion_discount',
        'ship_promotion_discount',
        'address_type',
        'ship_city',
        'ship_state',
        'ship_postal_code',
        'ship_country',
        'promotion_ids',
        'payment_method_details',
        'cpf',
        'item_extensions_data',
        'is_business_order',
        'purchase_order_number',
        'price_designation',
        'buyer_company_name',
        'is_replacement_order',
        'is_exchange_order',
        'original_order_id',
        'license_state',
        'license_expiration_date',
        'is_buyer_requested_cancellation',
        'buyer_requested_cancel_reason',
        'is_transparency',
        'ioss_number',
        'signature_confirmation_recommended'
    ]

    for col in req_columns:
        if col not in allOrdersDf.columns:
            allOrdersDf[col] = np.nan

    allOrdersDf = allOrdersDf[req_columns]

    schema = {
        'amazon_order_id': str,
        'merchant_order_id': str,
        'purchase_date': 'datetime64[ns, UTC]',
        'last_updated_date': 'datetime64[ns, UTC]',
        'order_status': str,
        'fulfillment_channel': str,
        'sales_channel': str,
        'order_channel': str,
        'ship_service_level': str,
        'product_name': str,
        'sku': str,
        'asin': str,
        'number_of_items': float,
        'item_status': str,
        'tax_collection_model': str,
        'tax_collection_responsible_party': str,
        'quantity': float,
        'currency': str,
        'item_price': float,
        'item_tax': float,
        'shipping_price': float,
        'shipping_tax': float,
        'gift_wrap_price': float,
        'gift_wrap_tax': float,
        'item_promotion_discount': float,
        'ship_promotion_discount': float,
        'address_type': str,
        'ship_city': str,
        'ship_state': str,
        'ship_postal_code': str,
        'ship_country': str,
        'promotion_ids': str,
        'payment_method_details': str,
        'cpf': str,
        'item_extensions_data': str,
        'is_business_order': bool,
        'purchase_order_number': str,
        'price_designation': str,
        'buyer_company_name': str,
        'is_replacement_order': bool,
        'is_exchange_order': bool,
        'original_order_id': str,
        'license_state': str,
        'license_expiration_date': str,
        'is_buyer_requested_cancellation': bool,
        'buyer_requested_cancel_reason': str,
        'is_transparency': bool,
        'ioss_number': str,
        'signature_confirmation_recommended': bool
    }

    allOrdersDf = allOrdersDf.astype(schema)

    return allOrdersDf

def inv_ledger_summary(marketplace_action, access_token, file_path_name, start_date, end_date, aggregateByLocation, aggregatedByTimePeriod):
    """
    This will pull inventory ledger report.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - start_date: start date (1989-09-05T00:00:00+00:00)
    - end_date: end date (1989-09-05T23:59:59+00:00)
    - aggregateByLocation: 'COUNTRY' or 'FC'
    - aggregatedByTimePeriod: 'MONTHLY', 'WEEKLY', 'DAILY'

    return:
    - data frame of inventory ledger summary report
    """

    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_LEDGER_SUMMARY_VIEW_DATA',
        'dataStartTime': start_date,
        'dataEndTime': end_date,
        'reportOptions': {
            'aggregateByLocation': aggregateByLocation,
            'aggregatedByTimePeriod': aggregatedByTimePeriod
        }
    }

    create_response = requests.post(url, headers=headers, json=request_params,)
    report_id = create_response.json()['reportId']

    document_id = _get_report_document_id(report_id, regionUrl, headers)

    # Download Report
    endpoint = f'/reports/2021-06-30/documents/{document_id}'
    url = regionUrl + endpoint
    document_response = requests.get(url, headers=headers)

    if document_response.status_code == 200:
        download_url = document_response.json()["url"]
        compression_algorithm = document_response.json().get("compressionAlgorithm")
        report_data = requests.get(download_url)

        if compression_algorithm == "GZIP":
            print('Decompressing...')

            with open(file_path_name + '.gz', 'wb') as f:
                f.write(report_data.content)

            with gzip.open(file_path_name + '.gz', 'rb') as f_in:
                with open(file_path_name, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        else:
            with open(file_path_name, 'wb') as f:
                f.write(report_data.content)

        print('Report Downloaded!')
    else:
        print("Failed to get the report document:", document_response.json())

    # Data Frame
    webhook_url = 'https://chat.googleapis.com/v1/spaces/AAAAq774XOA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=2-eECUKfzs1-UsiN3-YG6IV-DzwrDSIoS-bKmqU2qZY'

    try:
        ledgerDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        ledgerDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    ledgerDf = ledgerDf.rename(columns=lambda x:x.replace(' ','_').replace('/','_').lower())
    ledgerDf['date'] = pd.to_datetime(ledgerDf['date'])

    req_columns = [
        'date',
        'fnsku',
        'asin',
        'msku',
        'title',
        'disposition',
        'starting_warehouse_balance',
        'in_transit_between_warehouses',
        'receipts',
        'customer_shipments',
        'customer_returns',
        'vendor_returns',
        'warehouse_transfer_in_out',
        'found',
        'lost',
        'damaged',
        'disposed',
        'other_events',
        'ending_warehouse_balance',
        'unknown_events',
        'location',
        'store'
    ]

    add_col = [
        'store'
    ]

    for col in add_col:
        if col not in ledgerDf.columns:
            ledgerDf[col] = np.nan

    missing_col = set(req_columns) - set(ledgerDf.columns)
    new_col = set(ledgerDf.columns) - set(req_columns)
    if missing_col or new_col:
        formatted_message = f"""
        There are column changes for amazon inv_ledger_summary API report:
        missing columns: {missing_col}
        new columns: {new_col}
        """
        gchat_space(formatted_message, webhook_url)

    for col in req_columns:
        if col not in ledgerDf.columns:
            ledgerDf[col] = np.nan

    schema = {
        'date': 'datetime64[ns]',
        'fnsku': str,
        'asin': str,
        'msku': str,
        'title': str,
        'disposition': str,
        'starting_warehouse_balance': float,
        'in_transit_between_warehouses': float,
        'receipts': float,
        'customer_shipments': float,
        'customer_returns': float,
        'vendor_returns': float,
        'warehouse_transfer_in_out': float,
        'found': float,
        'lost': float,
        'damaged': float,
        'disposed': float,
        'other_events': float,
        'ending_warehouse_balance': float,
        'unknown_events': float,
        'location': str,
        'store': str
    }

    ledgerDf = ledgerDf.astype(schema)

    return ledgerDf

