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
import os
import urllib.parse
import json


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

def get_amz_report(
    marketplace_action,
    access_token,
    file_path_name,
    report_type,
    report_options=None,
    data_start_time=None,
    data_end_time=None,
    past_days=None
):
    """
    Generic function to request and download any Amazon SP-API report.
    
    Parameters:
    - marketplace_action: function that returns (regionUrl, marketplace_id)
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - report_type: the type of report (e.g., 'GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT')
    - report_options: dict of report-specific options (optional)
    - data_start_time: ISO 8601 datetime string for report start time (optional)
    - data_end_time: ISO 8601 datetime string for report end time (optional)
    - past_days: number of days from today's date (UTC) - alternative to data_start_time (optional)
    
    Returns:
    - file_path_name: path to the downloaded report file
    """
    
    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = '/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }
    
    # Build request parameters
    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': report_type
    }
    
    # Handle time parameters
    if data_start_time:
        request_params['dataStartTime'] = data_start_time
    elif past_days:
        request_params['dataStartTime'] = (
            datetime.now(timezone.utc) - timedelta(days=past_days)
        ).isoformat()
    
    if data_end_time:
        request_params['dataEndTime'] = data_end_time
    
    # Add report options if provided
    if report_options:
        request_params['reportOptions'] = report_options
    
    # Create the report
    print(f"Creating report: {report_type}")
    create_response = requests.post(url, headers=headers, json=request_params)
    
    if create_response.status_code != 202:
        raise ValueError(f"Failed to create report: {create_response.text}")
    
    report_id = create_response.json()['reportId']
    print(f"Report ID: {report_id}")
    
    # Wait for report to be ready and get document ID
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
        return file_path_name
    else:
        raise ValueError(f"Failed to get the report document: {document_response.json()}")

def zv_client_access(username, region):
    """
    This is authentication process for amazon.
    Only works for ZV Data Automation Clients
    """
    url = "https://zvdataautomation.com//zvapiauth/"
    payload = {"username": username, "region": region}
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        access_token = response.json()['access_token']
        print('Access Token granted 1 hour validity.')
        return access_token
    else:
        return ValueError('Error: Not Authenticated')
    
def shipment_status(marketplace_action, access_token, past_days):
    """
    This will pull all shipment and its status for specified marketplace

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of the list of shipments and its status
    """
    ShipmentStatusLists =[
        'WORKING', 'READY_TO_SHIP', 'SHIPPED', 'RECEIVING',
        'CANCELLED', 'DELETED', 'CLOSED', 'ERROR',
        'IN_TRANSIT', 'DELIVERED', 'CHECKED_IN'
    ]

    rate_limiter = RateLimiter(tokens_per_second=2, capacity=30)
    NextToken = None
    records = []

    regionUrl, MarketplaceId = marketplace_action()
    endpoint = '/fba/inbound/v0/shipments'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    LastUpdatedAfter = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()
    LastUpdatedBefore = datetime.now(timezone.utc).isoformat()

    for ShipmentStatusList in ShipmentStatusLists:
        request_params = {
            'MarketplaceId': MarketplaceId,
            'QueryType': 'DATE_RANGE',
            'ShipmentStatusList': ShipmentStatusList,
            'LastUpdatedAfter': LastUpdatedAfter,
            'LastUpdatedBefore': LastUpdatedBefore,
            'NextToken': NextToken
        }

        try:
            response = requests.get(url, headers=headers, params=request_params)
            records.extend(response.json()['payload']['ShipmentData'])

            try:
                NextToken = response.json()['payload']['NextToken']
            except:
                NextToken = None

            while NextToken:
                request_params_next = {
                    'MarketplaceId': MarketplaceId,
                    'QueryType': 'NEXT_TOKEN',
                    'NextToken': NextToken
                }
                response = rate_limiter.send_request(requests.get, url, headers=headers, params=request_params_next)
                records.extend(response.json()['payload']['ShipmentData'])

                try:
                    NextToken = response.json()['payload']['NextToken']
                except:
                    NextToken = None

            print('end of list')

        except Exception as e:
            raise ValueError(f'{response.status_code} - {response.text}')

    shipments = []
    for record in records:
        shipments.append({
            'shipment_id': record['ShipmentId'],
            'shipment_name': record['ShipmentName'],
            'shipment_status': record['ShipmentStatus'],
            'destination_fulfillment_center': record['DestinationFulfillmentCenterId']
        })

    df = pd.DataFrame(shipments)
    df['country'] = df['destination_fulfillment_center'].map(fc_to_country)

    return df

def shipment_items(marketplace_action, access_token, past_days):
    """
    This will pull all shipment and items inside it for specified marketplace.
    Together with the quantity shipped vs received

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of the list of shipments and items inside it
    """
    rate_limiter = RateLimiter(tokens_per_second=2, capacity=30)
    NextToken = None
    records = []


    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/fba/inbound/v0/shipmentItems'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    LastUpdatedAfter = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()
    LastUpdatedBefore = datetime.now(timezone.utc).isoformat()

    request_params = {
        'MarketplaceId': marketplace_id,
        'LastUpdatedAfter': LastUpdatedAfter,
        'LastUpdatedBefore': LastUpdatedBefore,
        'QueryType': 'DATE_RANGE'
    }
    
    try:
        response = requests.get(url, headers=headers, params=request_params)
        records.extend(response.json()['payload']['ItemData'])

        try:
            NextToken = response.json()['payload']['NextToken']
        except:
            NextToken = None

        while NextToken:
            request_params_next = {
                'MarketplaceId': marketplace_id,
                'QueryType': 'NEXT_TOKEN',
                'NextToken': NextToken
            }
            response = rate_limiter.send_request(requests.get, url, headers=headers, params=request_params_next)
            records.extend(response.json()['payload']['ItemData'])

            try:
                NextToken = response.json()['payload']['NextToken']
            except:
                NextToken = None

        print('end of list')

    except Exception as e:
        raise ValueError(f'{response.status_code} - {response.text}')

    df = []
    for record in records:

        if len(record['PrepDetailsList']) > 0:
            df.append({
                'shipment_id': record['ShipmentId'],
                'sku': record['SellerSKU'],
                'fnsku': record['FulfillmentNetworkSKU'],
                'shipped_qty': record['QuantityShipped'],
                'received_qty': record['QuantityReceived'],
                'case_qty': record['QuantityInCase'],
                'prep_instruction': record['PrepDetailsList'][0]['PrepInstruction'],
                'prep_owner': record['PrepDetailsList'][0]['PrepOwner']
            })
        else:
            df.append({
                'shipment_id': record['ShipmentId'],
                'sku': record['SellerSKU'],
                'fnsku': record['FulfillmentNetworkSKU'],
                'shipped_qty': record['QuantityShipped'],
                'received_qty': record['QuantityReceived'],
                'case_qty': record['QuantityInCase'],
                'prep_instruction': np.nan,
                'prep_owner': np.nan
            })
    shipmentItemsDf = pd.DataFrame(df)
    return shipmentItemsDf 

def shipment_summary(marketplace_action, access_token, past_days):
    """
    This will pull all shipment and items inside it for specified marketplace.
    And Summarise the Report

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of the report summary
    """
    shipmentDf = shipment_status(marketplace_action, access_token, past_days)
    shipmentItemsDf = shipment_items(marketplace_action, access_token, past_days)

    shipmentSummaryDf = shipmentDf.merge(shipmentItemsDf, how='inner', on='shipment_id')
    shipmentSummaryDf.insert(0,'date',datetime.now(timezone.utc).strftime('%F'))

    schema = {
        'date': 'datetime64[ns]',
        'shipment_id': str,
        'shipment_name': str,
        'shipment_status': str,
        'destination_fulfillment_center': str,
        'country': str,
        'sku': str,
        'fnsku': str,
        'shipped_qty': float,
        'received_qty': float,
        'case_qty': float,
        'prep_instruction': str,
        'prep_owner': str
    }
    shipmentSummaryDf = shipmentSummaryDf.astype(schema)

    return shipmentSummaryDf

def narf_eligibility(access_token, file_path_name):
    """
    This will pull the report for NARF eligibility of the SKUs

    Parameter:
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name

    return:
    - data frame of the NARF Eligibility report
    """
    # Create Report
    regionUrl, marketplace_id = marketplaces.US()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_REMOTE_FULFILLMENT_ELIGIBILITY'
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
        report_data = requests.get(download_url)

        with open(file_path_name, "wb") as f:
            f.write(report_data.content)
    else:
        print("Failed to get the report document:", document_response.json())

    #prepare DF
    narfDf = pd.read_excel(file_path_name,sheet_name='Enrollment',skiprows=3)
    narfDf = narfDf.rename(columns=lambda x:x.replace('.1','').replace('.2','').replace('(Yes/No)','')
                                    .replace(' Brazil ','').replace(' Canada ','').replace(' Mexico ','')
                                    .replace('/','_').replace(' ','_')
                                    .lower())

    brNarfDf = narfDf.iloc[:,:6]
    brNarfDf.insert(0,'marketplace','Brazil')

    caNarfDf = pd.concat([narfDf.iloc[:,:3],narfDf.iloc[:,6:9]], axis = 1)
    caNarfDf.insert(0,'marketplace','Canada')

    mxNarfDf = pd.concat([narfDf.iloc[:,:3],narfDf.iloc[:,9:12]], axis = 1)
    mxNarfDf.insert(0,'marketplace','Mexico')

    narfFinalDf = pd.concat([brNarfDf,caNarfDf,mxNarfDf], axis=0, ignore_index=True)
    narfFinalDf.insert(0,'date',datetime.now(timezone.utc).strftime('%F'))

    schema = {
        'date': 'datetime64[ns]',
    'marketplace': str,
    'merchant_sku': str,
    'asin': str,
    'product_name': str,
    'offer_status': str,
    'more_details': str,
    'enable_disable': str
    }

    narfFinalDf = narfFinalDf.astype(schema)

    return narfFinalDf

def fba_inventory(marketplace_action, access_token, file_path, marketplace_ids):
    """
    This will pull all FBA Inventory Report for the sepcified marketplaces

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path: the specific file path where to save the raw report Example: '/content'
    - marketplace_ids: lists of marketplace ids

    return:
    - data frame of FBA Inventory Report for all marketplaces
    """
    id_count = len(marketplace_ids)
    counter = 1
    # pulling of report
    for marketplace_id in marketplace_ids:
        print('Preparing for report request.')
        # set file path
        file_path_name = os.path.join(file_path, (marketplace_id + '_fbaInv.txt'))
        # Create Report
        regionUrl, mid = marketplace_action()
        endpoint = f'/reports/2021-06-30/reports'
        url = regionUrl + endpoint
        headers = {
            'x-amz-access-token': access_token,
            'Content-Type': 'application/json'
        }

        request_params = {
            'marketplaceIds': [marketplace_id],
            'reportType': 'GET_FBA_INVENTORY_PLANNING_DATA'
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
            report_data = requests.get(download_url)

            with open(file_path_name, "wb") as f:
                f.write(report_data.content)
        else:
            print("Failed to get the report document:", document_response.json())
        
        if counter < id_count:
            time.sleep(1200) #Wait before next report
            counter = counter + 1

    # create df
    fbaInvDf = []

    for marketplace_id in marketplace_ids:
        file_path_name = os.path.join(file_path, (marketplace_id + '_fbaInv.txt'))
        fbaInvInitDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
        fbaInvDf.append(fbaInvInitDf)

    fbaInvFinalDf = pd.concat(fbaInvDf, ignore_index=True)
    fbaInvFinalDf = fbaInvFinalDf.rename(columns=lambda x:x.replace('-','_').replace('?','').replace('(','')
                                        .replace(')','').replace(' ','').lower())

    req_columns = [
        'snapshot_date',
        'sku',
        'fnsku',
        'asin',
        'product_name',
        'condition',
        'available',
        'pending_removal_quantity',
        'inv_age_0_to_90_days',
        'inv_age_91_to_180_days',
        'inv_age_181_to_270_days',
        'inv_age_271_to_365_days',
        'inv_age_365_plus_days',
        'currency',
        'units_shipped_t7',
        'units_shipped_t30',
        'units_shipped_t60',
        'units_shipped_t90',
        'alert',
        'your_price',
        'sales_price',
        'lowest_price_new_plus_shipping',
        'lowest_price_used',
        'recommended_action',
        'deprecatedhealthy_inventory_level',
        'recommended_sales_price',
        'recommended_sale_duration_days',
        'recommended_removal_quantity',
        'estimated_cost_savings_of_recommended_actions',
        'sell_through',
        'item_volume',
        'volume_unit_measurement',
        'storage_type',
        'storage_volume',
        'marketplace',
        'product_group',
        'sales_rank',
        'days_of_supply',
        'estimated_excess_quantity',
        'weeks_of_cover_t30',
        'weeks_of_cover_t90',
        'featuredoffer_price',
        'sales_shipped_last_7_days',
        'sales_shipped_last_30_days',
        'sales_shipped_last_60_days',
        'sales_shipped_last_90_days',
        'inv_age_0_to_30_days',
        'inv_age_31_to_60_days',
        'inv_age_61_to_90_days',
        'inv_age_181_to_330_days',
        'inv_age_331_to_365_days',
        'estimated_storage_cost_next_month',
        'inbound_quantity',
        'inbound_working',
        'inbound_shipped',
        'inbound_received',
        'no_sale_last_6_months',
        'totalreservedquantity',
        'unfulfillable_quantity',
        'quantity_to_be_charged_ais_181_210_days',
        'estimated_ais_181_210_days',
        'quantity_to_be_charged_ais_211_240_days',
        'estimated_ais_211_240_days',
        'quantity_to_be_charged_ais_241_270_days',
        'estimated_ais_241_270_days',
        'quantity_to_be_charged_ais_271_300_days',
        'estimated_ais_271_300_days',
        'quantity_to_be_charged_ais_301_330_days',
        'estimated_ais_301_330_days',
        'quantity_to_be_charged_ais_331_365_days',
        'estimated_ais_331_365_days',
        'quantity_to_be_charged_ais_365_plus_days',
        'estimated_ais_365_plus_days',
        'historical_days_of_supply',
        'fba_minimum_inventory_level',
        'fba_inventory_level_health_status',
        'recommendedship_inquantity',
        'recommendedship_indate',
        'lastupdateddateforhistoricaldaysofsupply',
        'exemptedfromlow_inventory_levelfee',
        'low_inventory_levelfeeappliedincurrentweek',
        'shorttermhistoricaldaysofsupply',
        'longtermhistoricaldaysofsupply',
        'inventoryagesnapshotdate',
        'inventorysupplyatfba',
        'reservedfctransfer',
        'reservedfcprocessing',
        'reservedcustomerorder',
        'totaldaysofsupplyincludingunitsfromopenshipments',
        'healthy_inventory_level'
    ]

    for col in req_columns:
        if col not in fbaInvFinalDf.columns:
            fbaInvFinalDf[col] = np.nan

    fbaInvFinalDf = fbaInvFinalDf[req_columns]

    schema = {
        'snapshot_date': 'datetime64[ns]',
        'sku': str,
        'fnsku': str,
        'asin': str,
        'product_name': str,
        'condition': str,
        'available': float,
        'pending_removal_quantity': float,
        'inv_age_0_to_90_days': float,
        'inv_age_91_to_180_days': float,
        'inv_age_181_to_270_days': float,
        'inv_age_271_to_365_days': float,
        'inv_age_365_plus_days': float,
        'currency': str,
        'units_shipped_t7': float,
        'units_shipped_t30': float,
        'units_shipped_t60': float,
        'units_shipped_t90': float,
        'alert': str,
        'your_price': float,
        'sales_price': float,
        'lowest_price_new_plus_shipping': float,
        'lowest_price_used': float,
        'recommended_action': str,
        'deprecatedhealthy_inventory_level': float,
        'recommended_sales_price': float,
        'recommended_sale_duration_days': float,
        'recommended_removal_quantity': float,
        'estimated_cost_savings_of_recommended_actions': float,
        'sell_through': float,
        'item_volume': float,
        'volume_unit_measurement': str,
        'storage_type': str,
        'storage_volume': float,
        'marketplace': str,
        'product_group': str,
        'sales_rank': float,
        'days_of_supply': float,
        'estimated_excess_quantity': float,
        'weeks_of_cover_t30': float,
        'weeks_of_cover_t90': float,
        'featuredoffer_price': float,
        'sales_shipped_last_7_days': float,
        'sales_shipped_last_30_days': float,
        'sales_shipped_last_60_days': float,
        'sales_shipped_last_90_days': float,
        'inv_age_0_to_30_days': float,
        'inv_age_31_to_60_days': float,
        'inv_age_61_to_90_days': float,
        'inv_age_181_to_330_days': float,
        'inv_age_331_to_365_days': float,
        'estimated_storage_cost_next_month': float,
        'inbound_quantity': float,
        'inbound_working': float,
        'inbound_shipped': float,
        'inbound_received': float,
        'no_sale_last_6_months': float,
        'totalreservedquantity': float,
        'unfulfillable_quantity': float,
        'quantity_to_be_charged_ais_181_210_days': float,
        'estimated_ais_181_210_days': float,
        'quantity_to_be_charged_ais_211_240_days': float,
        'estimated_ais_211_240_days': float,
        'quantity_to_be_charged_ais_241_270_days': float,
        'estimated_ais_241_270_days': float,
        'quantity_to_be_charged_ais_271_300_days': float,
        'estimated_ais_271_300_days': float,
        'quantity_to_be_charged_ais_301_330_days': float,
        'estimated_ais_301_330_days': float,
        'quantity_to_be_charged_ais_331_365_days': float,
        'estimated_ais_331_365_days': float,
        'quantity_to_be_charged_ais_365_plus_days': float,
        'estimated_ais_365_plus_days': float,
        'historical_days_of_supply': float,
        'fba_minimum_inventory_level': float,
        'fba_inventory_level_health_status': str,
        'recommendedship_inquantity': float,
        'recommendedship_indate': 'datetime64[ns]',
        'lastupdateddateforhistoricaldaysofsupply': 'datetime64[ns]',
        'exemptedfromlow_inventory_levelfee': str,
        'low_inventory_levelfeeappliedincurrentweek': str,
        'shorttermhistoricaldaysofsupply': float,
        'longtermhistoricaldaysofsupply': float,
        'inventoryagesnapshotdate': 'datetime64[ns]',
        'inventorysupplyatfba': float,
        'reservedfctransfer': float,
        'reservedfcprocessing': float,
        'reservedcustomerorder': float,
        'totaldaysofsupplyincludingunitsfromopenshipments': float,
        'healthy_inventory_level': float
    }

    fbaInvFinalDf = fbaInvFinalDf.astype(schema)

    return fbaInvFinalDf

def all_orders(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull all orders report per region.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of all orders report
    """
    # Create Report
    regionUrl , marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL',
        'dataStartTime': dataStartTime
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

def reimbursement_report(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull reimbursement report per region.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of reimbursement report
    """
    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FBA_REIMBURSEMENTS_DATA',
        'dataStartTime': dataStartTime
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
    try:
        reimbursementDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        reimbursementDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    reimbursementDf = reimbursementDf.rename(columns=lambda x:x.replace('-','_').replace(' ','_').lower())
    reimbursementDf['approval_date'] = pd.to_datetime(reimbursementDf['approval_date'])

    req_columns = [
        'approval_date',
        'reimbursement_id',
        'case_id',
        'amazon_order_id',
        'reason',
        'sku',
        'fnsku',
        'asin',
        'product_name',
        'condition',
        'currency_unit',
        'amount_per_unit',
        'amount_total',
        'quantity_reimbursed_cash',
        'quantity_reimbursed_inventory',
        'quantity_reimbursed_total',
        'original_reimbursement_id',
        'original_reimbursement_type'
    ]

    for col in req_columns:
        if col not in reimbursementDf.columns:
            reimbursementDf[col] = np.nan

    reimbursementDf = reimbursementDf[req_columns]

    schema = {
        'approval_date': 'datetime64[ns, UTC]',
        'reimbursement_id': str,
        'case_id': str,
        'amazon_order_id': str,
        'reason': str,
        'sku': str,
        'fnsku': str,
        'asin': str,
        'product_name': str,
        'condition': str,
        'currency_unit': str,
        'amount_per_unit': float,
        'amount_total': float,
        'quantity_reimbursed_cash': float,
        'quantity_reimbursed_inventory': float,
        'quantity_reimbursed_total': float,
        'original_reimbursement_id': str,
        'original_reimbursement_type': str,
    }

    reimbursementDf = reimbursementDf.astype(schema)

    return reimbursementDf

def inv_ledger(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull inventory ledger report.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of inventory ledger report
    """

    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_LEDGER_DETAIL_VIEW_DATA',
        'dataStartTime': dataStartTime
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
    try:
        ledgerDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        ledgerDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    ledgerDf = ledgerDf.rename(columns=lambda x:x.replace(' ','_').lower())
    ledgerDf['date'] = pd.to_datetime(ledgerDf['date'])

    req_columns = [
        'date',
        'fnsku',
        'asin',
        'msku',
        'title',
        'event_type',
        'reference_id',
        'quantity',
        'fulfillment_center',
        'disposition',
        'reason',
        'country',
        'reconciled_quantity',
        'unreconciled_quantity',
        'date_and_time',
        'store'
    ]

    for col in req_columns:
        if col not in ledgerDf.columns:
            ledgerDf[col] = np.nan

    ledgerDf = ledgerDf[req_columns]

    schema = {
        'date': 'datetime64[ns]',
        'fnsku': str,
        'asin': str,
        'msku': str,
        'title': str,
        'event_type': str,
        'reference_id': str,
        'quantity': float,
        'fulfillment_center': str,
        'disposition': str,
        'reason': str,
        'country': str,
        'reconciled_quantity': float,
        'unreconciled_quantity': float,
        'date_and_time': 'datetime64[ns, UTC]',
        'store': str
    }

    ledgerDf = ledgerDf.astype(schema)

    return ledgerDf

def customer_return(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull customer return report.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of customer return report
    """

    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA',
        'dataStartTime': dataStartTime
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
    try:
        returnsDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        returnsDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    returnsDf = returnsDf.rename(columns=lambda x:x.replace('-','_').lower())
    returnsDf['return_date'] = pd.to_datetime(returnsDf['return_date'], utc=True)

    req_columns = [
        'return_date',
        'order_id',
        'sku',
        'asin',
        'fnsku',
        'product_name',
        'quantity',
        'fulfillment_center_id',
        'detailed_disposition',
        'reason',
        'status',
        'license_plate_number',
        'customer_comments'
    ]

    for col in req_columns:
        if col not in returnsDf.columns:
            returnsDf[col] = np.nan

    returnsDf = returnsDf[req_columns]

    schema = {
        'return_date': 'datetime64[ns, UTC]',
        'order_id': str,
        'sku': str,
        'asin': str,
        'fnsku': str,
        'product_name': str,
        'quantity': int,
        'fulfillment_center_id': str,
        'detailed_disposition': str,
        'reason': str,
        'status': str,
        'license_plate_number': str,
        'customer_comments': str
    }

    returnsDf = returnsDf.astype(schema)

    return returnsDf

def replacements(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull replacement report.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of replacement report
    """

    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FBA_FULFILLMENT_CUSTOMER_SHIPMENT_REPLACEMENT_DATA',
        'dataStartTime': dataStartTime
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
    try:
        replacementDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        replacementDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    replacementDf = replacementDf.rename(columns=lambda x:x.replace('-','_').lower())
    replacementDf['shipment_date'] = pd.to_datetime(replacementDf['shipment_date'], utc=True)
    replacementDf.info()

    req_columns = [
        'shipment_date',
        'sku',
        'asin',
        'fulfillment_center_id',
        'original_fulfillment_center_id',
        'quantity',
        'replacement_reason_code',
        'replacement_amazon_order_id',
        'original_amazon_order_id'
    ]

    for col in req_columns:
        if col not in replacementDf.columns:
            replacementDf[col] = np.nan

    replacementDf = replacementDf[req_columns]

    schema = {
        'shipment_date': 'datetime64[ns, UTC]',
        'sku': str,
        'asin': str,
        'fulfillment_center_id': str,
        'original_fulfillment_center_id': str,
        'quantity': float,
        'replacement_reason_code': float,
        'replacement_amazon_order_id': str,
        'original_amazon_order_id': str
    }

    replacementDf = replacementDf.astype(schema)

    return replacementDf

def offers(marketplace_action, access_token, asin_list):
    """
    This will pull offer details for each ASIN in the list.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - asin_list: list of all ASIN, should be in form of list

    return:
    - data frame of offer details of each ASIN
    """

    rate_limiter = RateLimiter(tokens_per_second=0.5, capacity=1)
    records = []
    regionUrl, marketplace_id = marketplace_action()

    for asin in asin_list:
        headers = {
                'x-amz-access-token': access_token
            }

        request_params  = {
            'MarketplaceId': marketplace_id,
            "ItemCondition": "New"
        }

        url = regionUrl + f'/products/pricing/v0/items/{asin}/offers' + '?' + urllib.parse.urlencode(request_params)

        response = rate_limiter.send_request(requests.get, url, headers=headers)
        records.extend([response.json()['payload']])

    offersInitDf = []

    for record in records:
        if not record['Offers']:
            offersInitDf.append({
                'seller_id': np.nan,
                'marketplace_id': record['Identifier']['MarketplaceId'],
                'asin': record['ASIN'],
                'item_condition': record['ItemCondition'],
                'currency': np.nan,
                'buybox_price': np.nan,
                'list_price': np.nan,
                'is_buybox_winner': np.nan
            })
        else:
            offersInitDf.append({
                'seller_id': record['Offers'][0]['SellerId'],
                'marketplace_id': record['Identifier']['MarketplaceId'],
                'asin': record['ASIN'],
                'item_condition': record['ItemCondition'],
                'currency': record['Summary']['BuyBoxPrices'][0]['ListingPrice']['CurrencyCode'],
                'buybox_price': record['Summary']['BuyBoxPrices'][0]['ListingPrice']['Amount'],
                'list_price': record['Offers'][0]['ListingPrice']['Amount'],
                'is_buybox_winner': record['Offers'][0]['IsBuyBoxWinner']
            })

    offersDf = pd.DataFrame(offersInitDf)

    return offersDf

def ss_forecast(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull S&S Forecast report.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of S&S Forecast report
    """

    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FBA_SNS_FORECAST_DATA',
        'dataStartTime': dataStartTime
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
    try:
        ssForcastDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        ssForcastDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    ssForcastDf = ssForcastDf.rename(columns=lambda x:x.replace('-','_').lower())
    ssForcastDf['snapshot_date'] = pd.to_datetime(ssForcastDf['snapshot_date'])
    ssForcastDf['week_1_start_date'] = pd.to_datetime(ssForcastDf['week_1_start_date'])
    ssForcastDf['estimated_avg_sns_discount_next_8_weeks'] = ssForcastDf['estimated_avg_sns_discount_next_8_weeks'].replace('%', '', regex=True).astype(float) / 100

    req_columns = [
        'offer_state',
        'snapshot_date',
        'sku',
        'fnsku',
        'asin',
        'estimated_avg_sns_discount_next_8_weeks',
        'product_name',
        'country',
        'active_subscriptions',
        'week_1_start_date',
        'scheduled_sns_units_week_1',
        'scheduled_sns_units_week_2',
        'scheduled_sns_units_week_3',
        'scheduled_sns_units_week_4',
        'scheduled_sns_units_week_5',
        'scheduled_sns_units_week_6',
        'scheduled_sns_units_week_7',
        'scheduled_sns_units_week_8'
    ]

    for col in req_columns:
        if col not in ssForcastDf.columns:
            ssForcastDf[col] = np.nan

    ssForcastDf = ssForcastDf[req_columns]

    schema = {
        'offer_state': str,
        'snapshot_date': 'datetime64[ns, UTC]',
        'sku': str,
        'fnsku': str,
        'asin': str,
        'estimated_avg_sns_discount_next_8_weeks': float,
        'product_name': str,
        'country': str,
        'active_subscriptions': float,
        'week_1_start_date': 'datetime64[ns, UTC]',
        'scheduled_sns_units_week_1': float,
        'scheduled_sns_units_week_2': float,
        'scheduled_sns_units_week_3': float,
        'scheduled_sns_units_week_4': float,
        'scheduled_sns_units_week_5': float,
        'scheduled_sns_units_week_6': float,
        'scheduled_sns_units_week_7': float,
        'scheduled_sns_units_week_8': float
    }
    ssForcastDf = ssForcastDf.astype(schema)

    return ssForcastDf

def ss_performance(marketplace_action, access_token, past_weeks):
    """
    This will pull S&S Performance report.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - past_weeks: number of weeks from today's date (UTC)

    return:
    - data frame of S&S Performance report
    """
    weeks = []
    today = datetime.now(timezone.utc)
    regionUrl, marketplace_id = marketplace_action()

    # Find last Saturday
    days_since_saturday = (today.weekday() - 5) % 7
    last_saturday = today - timedelta(days=days_since_saturday)
    last_saturday = last_saturday.replace(hour=23, minute=59, second=59, microsecond=0)

    for i in range(past_weeks):
        end_date = last_saturday - timedelta(weeks=i)
        start_date = end_date - timedelta(days=6)

        weeks.append({
            "startDate": start_date.strftime("%Y-%m-%dT00:00:00.000Z"),
            "endDate": end_date.strftime("%Y-%m-%dT23:59:59.000Z")
        })

    # Pull API Data
    dfFinal = []
    for week in weeks:
        startDate = week.get('startDate')
        endDate = week.get('endDate')
        url = "https://sellingpartnerapi-na.amazon.com/replenishment/2022-11-07/offers/metrics/search"

        payload = {
            "pagination": {
                "limit": 500,
                "offset": 0
            },
            "sort": {
                "order": "ASC",
                "key": "SHIPPED_SUBSCRIPTION_UNITS"
            },
            "filters": {
                "aggregationFrequency": "WEEK",
                "timeInterval": {
                    "startDate": startDate,
                    "endDate": endDate
                },
                "timePeriodType": "PERFORMANCE",
                "marketplaceId": marketplace_id,
                "programTypes": ["SUBSCRIBE_AND_SAVE"]
            }
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            'x-amz-access-token': access_token
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"Error: {response.errors}")
            break

        df = pd.json_normalize(response.json().get('offers',[]))
        dfFinal.append(df)

    dfFinal = pd.concat(dfFinal, ignore_index=True)

    # Data Frame
    dfFormat = dfFinal.rename(columns=lambda x:x.replace('-','_').replace(' ','_').replace('.','_').lower())

    dfFormat['timeinterval_startdate'] = pd.to_datetime(dfFormat['timeinterval_startdate'])
    dfFormat['timeinterval_enddate'] = pd.to_datetime(dfFormat['timeinterval_enddate'])

    req_columns = [
        'shareofcouponsubscriptions',
        'asin',
        'activesubscriptions',
        'currencycode',
        'timeinterval_enddate',
        'timeinterval_startdate',
        'notdeliveredduetooos',
        'shippedsubscriptionunits',
        'lostrevenueduetooos',
        'totalsubscriptionsrevenue',
        'revenuepenetration',
        'couponsrevenuepenetration'
    ]

    missing_col = set(req_columns) - set(dfFormat.columns)
    new_col = set(dfFormat.columns) - set(req_columns)

    if missing_col:
        raise ValueError(f"Missing columns: {', '.join(missing_col)}")

    if new_col:
        print(f"New columns: {', '.join(new_col)}")

    dfFormat = dfFormat[req_columns]

    schema = {
        'shareofcouponsubscriptions': float,
        'asin': str,
        'activesubscriptions': float,
        'currencycode': str,
        'timeinterval_enddate': 'datetime64[ns, UTC]',
        'timeinterval_startdate': 'datetime64[ns, UTC]',
        'notdeliveredduetooos': float,
        'shippedsubscriptionunits': float,
        'lostrevenueduetooos': float,
        'totalsubscriptionsrevenue': float,
        'revenuepenetration': float,
        'couponsrevenuepenetration': float
    }

    dfFormat = dfFormat.astype(schema)
    return dfFormat

def finance_shipmentEventList(marketplace_action, access_token, past_days):
    """
    This will pull Shipment Event List in a region.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of shipment event reports
    """
    # Pull API Data
    rate_limiter = RateLimiter(tokens_per_second=0.5, capacity=30)
    records = []
    regionUrl, marketplace_id = marketplace_action()
    NextToken = None

    PostedAfter = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    headers = {
            'x-amz-access-token': access_token
        }

    request_params  = {
        'PostedAfter': PostedAfter
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
        raise ValueError(f'{response.status_code} - {response.text}')

    # set Data Frame
    taxDf = []
    for record in records:
        data ={
            'amazon_order_id': record.get('AmazonOrderId', np.nan),
            'posted_date': record.get('PostedDate', np.nan),
            'marketplace': record.get('MarketplaceName', np.nan),
            'sku': record.get('ShipmentItemList', [{}])[0].get('SellerSKU', np.nan),
            'qty': record.get('ShipmentItemList', [{}])[0].get('QuantityShipped', np.nan),
            'currency': record.get('ShipmentItemList', [{}])[0].get('ItemFeeList', [{}])[0].get('FeeAmount',{}).get('CurrencyCode', np.nan),
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

def fba_inv_live(marketplace_action, access_token):
    """
    This will pull Live Inventory in specific Marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace

    return:
    - data frame of the Live Inventory Count
    """
    # API Pull
    rate_limiter = RateLimiter(tokens_per_second=2, capacity=2)
    records = []
    regionUrl, marketplace_id = marketplace_action()
    NextToken = None
    url = regionUrl + f'/fba/inventory/v1/summaries'

    headers = {
            'x-amz-access-token': access_token
        }

    request_params  = {
        'granularityType': 'Marketplace',
        'granularityId': marketplace_id,
        'marketplaceIds': marketplace_id,
        'details': True
    }

    try:
        response = requests.get(url, headers=headers, params=request_params)
        records.extend(response.json()['payload']['inventorySummaries'])

        try:
            NextToken = response.json()['pagination']['nextToken']
        except:
            NextToken = None

        while NextToken:
            paginated_params  = {
                'granularityType': 'Marketplace',
                'granularityId': marketplace_id,
                'marketplaceIds': marketplace_id,
                'details': True,
                'nextToken': NextToken
            }
            response = rate_limiter.send_request(requests.get, url, headers=headers, params=paginated_params)
            records.extend(response.json()['payload']['inventorySummaries'])

            try:
                NextToken = response.json()['pagination']['nextToken']
            except:
                NextToken = None

        print('End of List')

    except Exception as e:
        raise ValueError(f'{response.status_code} - {response.text}')

    # Data Frame
    fbaInventoryDf = []

    for record in records:
        if record.get('lastUpdatedTime') != '':
            data = {
                'update_date': record.get('lastUpdatedTime', np.nan),
                'asin': record.get('asin', np.nan),
                'fnsku': record.get('fnSku', np.nan),
                'sellerSku': record.get('sellerSku', np.nan),
                'product_name': record.get('productName', np.nan),
                'condition': record.get('condition', np.nan),
                'total_qty': record.get('totalQuantity', np.nan),
                'fulfillable_qty': record.get('inventoryDetails',{}).get('fulfillableQuantity', np.nan),
                'inbound_working_qty': record.get('inventoryDetails',{}).get('inboundWorkingQuantity', np.nan),
                'inbound_shipped_qty': record.get('inventoryDetails',{}).get('inboundShippedQuantity', np.nan),
                'inbound_receiving_qty': record.get('inventoryDetails',{}).get('inboundReceivingQuantity', np.nan),
                'total_reserved_qty': record.get('inventoryDetails',{}).get('reservedQuantity', {}).get('totalReservedQuantity', np.nan),
                'customer_reserved_qty': record.get('inventoryDetails',{}).get('reservedQuantity', {}).get('pendingCustomerOrderQuantity', np.nan),
                'fc_transfer_qty': record.get('inventoryDetails',{}).get('reservedQuantity', {}).get('pendingTransshipmentQuantity', np.nan),
                'fc_processing_qty': record.get('inventoryDetails',{}).get('reservedQuantity', {}).get('fcProcessingQuantity', np.nan),
                'total_researching_qty': record.get('inventoryDetails',{}).get('researchingQuantity', {}).get('totalResearchingQuantity', np.nan),
                'total_unfulfillable_qty': record.get('inventoryDetails',{}).get('unfulfillableQuantity', {}).get('totalUnfulfillableQuantity', np.nan),
                'customer_damaged_qty': record.get('inventoryDetails',{}).get('unfulfillableQuantity', {}).get('customerDamagedQuantity', np.nan),
                'warehouse_damaged_qty': record.get('inventoryDetails',{}).get('unfulfillableQuantity', {}).get('warehouseDamagedQuantity', np.nan),
                'distribution_damaged_qty': record.get('inventoryDetails',{}).get('unfulfillableQuantity', {}).get('distributorDamagedQuantity', np.nan),
                'carrier_damaged_qty': record.get('inventoryDetails',{}).get('unfulfillableQuantity', {}).get('carrierDamagedQuantity', np.nan),
                'defective_qty': record.get('inventoryDetails',{}).get('unfulfillableQuantity', {}).get('defectiveQuantity', np.nan),
                'expired_qty': record.get('inventoryDetails',{}).get('unfulfillableQuantity', {}).get('expiredQuantity', np.nan),
                'reserved_future_qty': record.get('inventoryDetails',{}).get('futureSupplyQuantity', {}).get('reservedFutureSupplyQuantity', np.nan),
                'buyable_future_qty': record.get('inventoryDetails',{}).get('futureSupplyQuantity', {}).get('futureSupplyBuyableQuantity', np.nan),
            }

            for r in record.get('inventoryDetails',{}).get('researchingQuantity', {}).get('researchingQuantityBreakdown', []):
                data[r.get('name')] = r.get('quantity')

            fbaInventoryDf.append(data)

    fbaInventoryDf = pd.DataFrame(fbaInventoryDf)

    fbaInventoryDf['update_date'] = pd.to_datetime(fbaInventoryDf['update_date'])

    req_columns = [
        'update_date',
        'asin',
        'fnsku',
        'sellerSku',
        'product_name',
        'condition',
        'total_qty',
        'fulfillable_qty',
        'inbound_working_qty',
        'inbound_shipped_qty',
        'inbound_receiving_qty',
        'total_reserved_qty',
        'customer_reserved_qty',
        'fc_transfer_qty',
        'fc_processing_qty',
        'total_researching_qty',
        'total_unfulfillable_qty',
        'customer_damaged_qty',
        'warehouse_damaged_qty',
        'distribution_damaged_qty',
        'carrier_damaged_qty',
        'defective_qty',
        'expired_qty',
        'reserved_future_qty',
        'buyable_future_qty',
        'researchingQuantityInShortTerm',
        'researchingQuantityInMidTerm',
        'researchingQuantityInLongTerm'
    ]

    for col in req_columns:
        if col not in fbaInventoryDf.columns:
            fbaInventoryDf[col] = np.nan

    fbaInventoryDf = fbaInventoryDf[req_columns]

    schema = {
        'update_date': 'datetime64[ns, UTC]',
        'asin': str,
        'fnsku': str,
        'sellerSku': str,
        'product_name': str,
        'condition': str,
        'total_qty': float,
        'fulfillable_qty': float,
        'inbound_working_qty': float,
        'inbound_shipped_qty': float,
        'inbound_receiving_qty': float,
        'total_reserved_qty': float,
        'customer_reserved_qty': float,
        'fc_transfer_qty': float,
        'fc_processing_qty': float,
        'total_researching_qty': float,
        'total_unfulfillable_qty': float,
        'customer_damaged_qty': float,
        'warehouse_damaged_qty': float,
        'distribution_damaged_qty': float,
        'carrier_damaged_qty': float,
        'defective_qty': float,
        'expired_qty': float,
        'reserved_future_qty': float,
        'buyable_future_qty': float,
        'researchingQuantityInShortTerm': float,
        'researchingQuantityInMidTerm': float,
        'researchingQuantityInLongTerm': float
    }

    fbaInventoryDf = fbaInventoryDf.astype(schema)

    return fbaInventoryDf

def safe_get(data, *keys, default=np.nan):
    """
    Safely navigate nested dictionaries and lists.
    Returns default if any key doesn't exist, is None, or if list index is out of range.
    """
    result = data
    for key in keys:
        if result is None:
            return default
        if isinstance(key, int):  # List index
            if not isinstance(result, list) or len(result) <= key:
                return default
            result = result[key]
        else:  # Dictionary key
            if not isinstance(result, dict):
                return default
            result = result.get(key)
    return result if result is not None else default

def sku_attributes(marketplace_action, access_token, sellerId, sku_list):
    """
    This will pull SKU attributes in specific Marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - sellerId: the Seller ID of specific region
    - sku_list: list of all the SKUs to pull the attribute details

    return:
    - data frame of the attributes of all the SKU in the list
    """
    # API Pull
    rate_limiter = RateLimiter(tokens_per_second=5, capacity=10)
    records = []
    regionUrl, marketplace_id = marketplace_action()

    for sku in sku_list:
        url = regionUrl + f'/listings/2021-08-01/items/{sellerId}/{sku}'
        headers = {
                'x-amz-access-token': access_token
            }

        request_params  = {
            'marketplaceIds': marketplace_id,
            'includedData': 'attributes'
        }

        try:
            response =  rate_limiter.send_request(requests.get, url, headers=headers, params=request_params)
            records.extend([response.json()])

        except Exception as e:
            print(f'{response.status_code} - {response.text}')

    # Data Frame
    attributesDf = []
    for record in records:
        if record.get('sku') is not None:
            print(f'Processing SKU: {record.get("sku")}')
            
            attrs = record.get('attributes', {})
            
            data = {
                'sku': record.get('sku'),
                'item_name': safe_get(attrs, 'item_name', 0, 'value'),
                'color': safe_get(attrs, 'color', 0, 'value'),
                'variation_theme': safe_get(attrs, 'variation_theme', 0, 'name'),
                'item_package_weight': safe_get(attrs, 'item_package_weight', 0, 'value'),
                'item_package_weight_unit': safe_get(attrs, 'item_package_weight', 0, 'unit'),
                'manufacturer': safe_get(attrs, 'manufacturer', 0, 'value'),
                'product_description': safe_get(attrs, 'product_description', 0, 'value'),
                'brand': safe_get(attrs, 'brand', 0, 'value'),
                'generic_keyword': safe_get(attrs, 'generic_keyword', 0, 'value'),
                'item_type_keyword': safe_get(attrs, 'item_type_keyword', 0, 'value'),
                'condition_type': safe_get(attrs, 'condition_type', 0, 'value'),
                'number_of_items': safe_get(attrs, 'number_of_items', 0, 'value'),
                'height': safe_get(attrs, 'item_package_dimensions', 0, 'height', 'value'),
                'height_unit': safe_get(attrs, 'item_package_dimensions', 0, 'height', 'unit'),
                'length': safe_get(attrs, 'item_package_dimensions', 0, 'length', 'value'),
                'length_unit': safe_get(attrs, 'item_package_dimensions', 0, 'length', 'unit'),
                'width': safe_get(attrs, 'item_package_dimensions', 0, 'width', 'value'),
                'width_unit': safe_get(attrs, 'item_package_dimensions', 0, 'width', 'unit'),
                'size': safe_get(attrs, 'size', 0, 'value'),
                'max_order_quantity': safe_get(attrs, 'max_order_quantity', 0, 'value'),
                'main_image': safe_get(attrs, 'main_product_image_locator', 0, 'media_location'),
                'other_image_1': safe_get(attrs, 'other_product_image_locator_1', 0, 'media_location'),
                'other_image_2': safe_get(attrs, 'other_product_image_locator_2', 0, 'media_location'),
                'other_image_3': safe_get(attrs, 'other_product_image_locator_3', 0, 'media_location'),
                'other_image_4': safe_get(attrs, 'other_product_image_locator_4', 0, 'media_location'),
                'other_image_5': safe_get(attrs, 'other_product_image_locator_5', 0, 'media_location'),
                'other_image_6': safe_get(attrs, 'other_product_image_locator_6', 0, 'media_location'),
                'swatch_image': safe_get(attrs, 'swatch_product_image_locator', 0, 'media_location'),
                'list_price': safe_get(attrs, 'list_price', 0, 'value'),
                'list_price_currency': safe_get(attrs, 'list_price', 0, 'currency'),
                'offer_start_date': safe_get(attrs, 'purchasable_offer', 0, 'start_at', 'value'),
                'offer_end_date': safe_get(attrs, 'purchasable_offer', 0, 'end_at', 'value'),
                'offer_currency': safe_get(attrs, 'purchasable_offer', 0, 'currency'),
                'offer_audience': safe_get(attrs, 'purchasable_offer', 0, 'audience'),
                'your_price': safe_get(attrs, 'purchasable_offer', 0, 'our_price', 0, 'schedule', 0, 'value_with_tax'),
                'maximum_seller_allowed_price': safe_get(attrs, 'purchasable_offer', 0, 'maximum_seller_allowed_price', 0, 'schedule', 0, 'value_with_tax'),
                'minimum_seller_allowed_price': safe_get(attrs, 'purchasable_offer', 0, 'minimum_seller_allowed_price', 0, 'schedule', 0, 'value_with_tax'),
                'sale_start_date': safe_get(attrs, 'purchasable_offer', 0, 'discounted_price', 0, 'schedule', 0, 'start_at'),
                'sale_end_date': safe_get(attrs, 'purchasable_offer', 0, 'discounted_price', 0, 'schedule', 0, 'end_at'),
                'sale_price': safe_get(attrs, 'purchasable_offer', 0, 'discounted_price', 0, 'schedule', 0, 'value_with_tax'),
                'parentage_level': safe_get(attrs, 'parentage_level', 0, 'value'),
                'child_relationship_type': safe_get(attrs, 'child_parent_sku_relationship', 0, 'child_relationship_type'),
                'parent_sku': safe_get(attrs, 'child_parent_sku_relationship', 0, 'parent_sku'),
            }

            # Handle bullet points
            for i in range(5):
                data[f'bullet_point_{i + 1}'] = safe_get(attrs, 'bullet_point', i, 'value')

            attributesDf.append(data)

    attributesDf = pd.DataFrame(attributesDf)
    attributesDf.insert(0,'date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))

    req_columns = [
        'date',
        'sku',
        'item_name',
        'color',
        'variation_theme',
        'item_package_weight',
        'item_package_weight_unit',
        'manufacturer',
        'bullet_point_1',
        'bullet_point_2',
        'bullet_point_3',
        'bullet_point_4',
        'bullet_point_5',
        'product_description',
        'brand',
        'generic_keyword',
        'item_type_keyword',
        'condition_type',
        'number_of_items',
        'height',
        'height_unit',
        'length',
        'length_unit',
        'width',
        'width_unit',
        'size',
        'max_order_quantity',
        'main_image',
        'other_image_1',
        'other_image_2',
        'other_image_3',
        'other_image_4',
        'other_image_5',
        'other_image_6',
        'swatch_image',
        'list_price',
        'list_price_currency',
        'offer_start_date',
        'offer_end_date',
        'offer_currency',
        'offer_audience',
        'your_price',
        'maximum_seller_allowed_price',
        'minimum_seller_allowed_price',
        'sale_start_date',
        'sale_end_date',
        'sale_price',
        'parentage_level',
        'child_relationship_type',
        'parent_sku'
    ]

    for col in req_columns:
        if col not in attributesDf.columns:
            attributesDf[col] = np.nan

    attributesDf = attributesDf[req_columns]

    colPrices = ['list_price','your_price','minimum_seller_allowed_price','maximum_seller_allowed_price','sale_price']

    for colPrice in colPrices:
        attributesDf[colPrice] = attributesDf[colPrice].astype(str).replace({',': '.'}, regex=True)
        attributesDf[colPrice] = pd.to_numeric(attributesDf[colPrice], errors='coerce')

    schema = {
        'date': 'datetime64[ns]',
        'sku': str,
        'item_name': str,
        'color': str,
        'variation_theme': str,
        'item_package_weight': float,
        'item_package_weight_unit': str,
        'manufacturer': str,
        'bullet_point_1': str,
        'bullet_point_2': str,
        'bullet_point_3': str,
        'bullet_point_4': str,
        'bullet_point_5': str,
        'product_description': str,
        'brand': str,
        'generic_keyword': str,
        'item_type_keyword': str,
        'condition_type': str,
        'number_of_items': float,
        'height': float,
        'height_unit': str,
        'length': float,
        'length_unit': str,
        'width': float,
        'width_unit': str,
        'size': str,
        'max_order_quantity': float,
        'main_image': str,
        'other_image_1': str,
        'other_image_2': str,
        'other_image_3': str,
        'other_image_4': str,
        'other_image_5': str,
        'other_image_6': str,
        'swatch_image': str,
        'list_price': float,
        'list_price_currency': str,
        'offer_start_date': str,
        'offer_end_date': str,
        'offer_currency': str,
        'offer_audience': str,
        'your_price': float,
        'maximum_seller_allowed_price': float,
        'minimum_seller_allowed_price': float,
        'sale_start_date': str,
        'sale_end_date': str,
        'sale_price': float,
        'parentage_level': str,
        'child_relationship_type': str,
        'parent_sku': str
    }

    attributesDf = attributesDf.astype(schema)

    return attributesDf

def get_sellerId(marketplace_action, access_token, sku):
    """
    This will pull SKU attributes in specific Marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - sku: sample SKU that is active in the specific region

    return:
    - returns the Seller ID in a specific region
    """
    # API Pull
    rate_limiter = RateLimiter(tokens_per_second=0.5, capacity=1)
    regionUrl, marketplace_id = marketplace_action()

    url = regionUrl + f'/products/pricing/v0/competitivePrice'
    headers = {
            'x-amz-access-token': access_token
        }

    request_params  = {
        'MarketplaceId': marketplace_id,
        'Skus': sku,
        'ItemType': 'Sku'

    }

    try:
        response =  rate_limiter.send_request(requests.get, url, headers=headers, params=request_params)
        sellerId = (response.json().get('payload',[{}])[0].get('Product',{}).get('Identifiers',{}).get('SKUIdentifier',{}).get('SellerId', np.nan))
        return sellerId

    except Exception as e:
        print(e)
        raise ValueError(f'{response.status_code} - {response.text}')

def finance_refunds(marketplace_action, access_token, past_days):
    """
    This will pull refund List in a region.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of refunds report
    """
    # Pull API Data
    rate_limiter = RateLimiter(tokens_per_second=0.5, capacity=30)
    records = []
    regionUrl, marketplace_id = marketplace_action()
    NextToken = None

    PostedAfter = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    headers = {
            'x-amz-access-token': access_token
        }

    request_params  = {
        'PostedAfter': PostedAfter
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
        raise ValueError(f'{response.status_code} - {response.text}')

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

def fee_preview(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull Fee Preview Report for the sepcified region

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of FBA Fee Perview Report for the specified region
    """

    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FBA_ESTIMATED_FBA_FEES_TXT_DATA',
        'dataStartTime': dataStartTime
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
    try:
        feePreviewDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        feePreviewDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    feePreviewDf = feePreviewDf.rename(columns=lambda x:x.replace('-','_').lower())
    feePreviewDf = feePreviewDf.replace({'--':np.nan}, regex=True)

    req_columns = [
        'sku',
        'fnsku',
        'asin',
        'amazon_store',
        'product_name',
        'product_group',
        'brand',
        'fulfilled_by',
        'your_price',
        'sales_price',
        'longest_side',
        'median_side',
        'shortest_side',
        'length_and_girth',
        'unit_of_dimension',
        'item_package_weight',
        'unit_of_weight',
        'product_size_tier',
        'currency',
        'estimated_fee_total',
        'estimated_referral_fee_per_unit',
        'estimated_variable_closing_fee',
        'estimated_order_handling_fee_per_order',
        'estimated_pick_pack_fee_per_unit',
        'estimated_weight_handling_fee_per_unit',
        'expected_fulfillment_fee_per_unit',
        'has_local_inventory',
        'product_size_weight_band',
        'expected_domestic_fulfilment_fee_per_unit',
        'expected_efn_fulfilment_fee_per_unit_uk',
        'expected_efn_fulfilment_fee_per_unit_de',
        'expected_efn_fulfilment_fee_per_unit_fr',
        'expected_efn_fulfilment_fee_per_unit_it',
        'expected_efn_fulfilment_fee_per_unit_es',
        'expected_efn_fulfilment_fee_per_unit_se'
    ]

    for col in req_columns:
        if col not in feePreviewDf.columns:
            feePreviewDf[col] = np.nan

    feePreviewDf = feePreviewDf[req_columns]
    feePreviewDf.insert(0, 'snapshot_date', datetime.now(timezone.utc))

    schema = {
        'snapshot_date': 'datetime64[ns, UTC]',
        'sku': str,
        'fnsku': str,
        'asin': str,
        'amazon_store': str,
        'product_name': str,
        'product_group': str,
        'brand': str,
        'fulfilled_by': str,
        'your_price': float,
        'sales_price': float,
        'longest_side': float,
        'median_side': float,
        'shortest_side': float,
        'length_and_girth': float,
        'unit_of_dimension': str,
        'item_package_weight': float,
        'unit_of_weight': str,
        'product_size_tier': str,
        'currency': str,
        'estimated_fee_total': float,
        'estimated_referral_fee_per_unit': float,
        'estimated_variable_closing_fee': float,
        'estimated_order_handling_fee_per_order': float,
        'estimated_pick_pack_fee_per_unit': float,
        'estimated_weight_handling_fee_per_unit': float,
        'expected_fulfillment_fee_per_unit': float,
        'has_local_inventory': str,
        'product_size_weight_band': str,
        'expected_domestic_fulfilment_fee_per_unit': float,
        'expected_efn_fulfilment_fee_per_unit_uk': float,
        'expected_efn_fulfilment_fee_per_unit_de': float,
        'expected_efn_fulfilment_fee_per_unit_fr': float,
        'expected_efn_fulfilment_fee_per_unit_it': float,
        'expected_efn_fulfilment_fee_per_unit_es': float,
        'expected_efn_fulfilment_fee_per_unit_se': float
    }

    feePreviewDf = feePreviewDf.astype(schema)

    return feePreviewDf

def manage_fba(marketplace_action, access_token, file_path_name, past_days):
    """
    This will pull FBA Manaage Inventory report per region.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - past_days: number of days from today's date (UTC)

    return:
    - data frame of FBA Manage Inventory Report
    """
    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA',
        'dataStartTime': dataStartTime
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
    try:
        manageInvDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        manageInvDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    manageInvDf = manageInvDf.rename(columns=lambda x:x.replace('-','_').lower())

    req_columns = [
        'sku',
        'fnsku',
        'asin',
        'product_name',
        'condition',
        'your_price',
        'mfn_listing_exists',
        'mfn_fulfillable_quantity',
        'afn_listing_exists',
        'afn_warehouse_quantity',
        'afn_fulfillable_quantity',
        'afn_unsellable_quantity',
        'afn_reserved_quantity',
        'afn_total_quantity',
        'per_unit_volume',
        'afn_inbound_working_quantity',
        'afn_inbound_shipped_quantity',
        'afn_inbound_receiving_quantity',
        'afn_researching_quantity',
        'afn_reserved_future_supply',
        'afn_future_supply_buyable',
        'store',
        'afn_fulfillable_quantity_local',
        'afn_fulfillable_quantity_remote'
    ]

    for col in req_columns:
        if col not in manageInvDf.columns:
            manageInvDf[col] = np.nan

    manageInvDf = manageInvDf[req_columns]
    manageInvDf.insert(0, 'snapshot_date', datetime.now(timezone.utc))

    schema = {
        'snapshot_date': 'datetime64[ns, UTC]',
        'sku': str,
        'fnsku': str,
        'asin': str,
        'product_name': str,
        'condition': str,
        'your_price': float,
        'mfn_listing_exists': str,
        'mfn_fulfillable_quantity': float,
        'afn_listing_exists': str,
        'afn_warehouse_quantity': float,
        'afn_fulfillable_quantity': float,
        'afn_unsellable_quantity': float,
        'afn_reserved_quantity': float,
        'afn_total_quantity': float,
        'per_unit_volume': float,
        'afn_inbound_working_quantity': float,
        'afn_inbound_shipped_quantity': float,
        'afn_inbound_receiving_quantity': float,
        'afn_researching_quantity': float,
        'afn_reserved_future_supply': float,
        'afn_future_supply_buyable': float,
        'store': str,
        'afn_fulfillable_quantity_local': float,
        'afn_fulfillable_quantity_remote': float
    }

    manageInvDf = manageInvDf.astype(schema)

    return manageInvDf

def awd_inventory(marketplace_action, access_token):
    """
    This will pull AWD Inventory data per region.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace

    return:
    - data frame of AWD Inventory Data
    """
    # Pull API Data
    rate_limiter = RateLimiter(tokens_per_second=2, capacity=2)
    records = []
    regionUrl, marketplace_id = marketplace_action()
    NextToken = None

    headers = {
            'x-amz-access-token': access_token
        }

    request_params  = {
        'details': 'SHOW'
    }

    try:
        url = regionUrl + f'/awd/2024-05-09/inventory' + '?' + urllib.parse.urlencode(request_params)
        response = requests.get(url, headers=headers)
        records.extend(response.json()['inventory'])

        try:
            NextToken = response.json()['nextToken']
        except:
            NextToken = None

        while NextToken:
            request_params_next  = {
                'details': 'SHOW',
                'nextToken': NextToken
            }
            url = regionUrl + f'/awd/2024-05-09/inventory' + '?' + urllib.parse.urlencode(request_params_next)
            response = rate_limiter.send_request(requests.get, url, headers=headers)
            records.extend(response.json()['inventory'])

            try:
                NextToken = response.json()['nextToken']
            except:
                NextToken = None

        print('End of List')

    except Exception as e:
        raise ValueError(f'{response.status_code} - {response.text}')

    # Dataframe
    awdDf = []
    for record in records:
        if record.get('sku') is not None:
            data = {
                'sku': record.get('sku'),
                'total_onhand_qty': record.get('totalOnhandQuantity', np.nan),
                'total_inbound_qty': record.get('totalInboundQuantity', np.nan),
                'reserved_distributable_qty': record.get('inventoryDetails',{}).get('reservedDistributableQuantity', np.nan),
                'available_distributable_qty': record.get('inventoryDetails',{}).get('availableDistributableQuantity', np.nan)
            }
            awdDf.append(data)

    awdDf = pd.DataFrame(awdDf)
    awdDf.insert(0, 'snapshot_date', datetime.now(timezone.utc))

    req_columns = [
        'snapshot_date',
        'sku',
        'total_onhand_qty',
        'total_inbound_qty',
        'reserved_distributable_qty',
        'available_distributable_qty'
    ]

    for col in req_columns:
        if col not in awdDf.columns:
            awdDf[col] = np.nan

    awdDf = awdDf[req_columns]

    schema = {
        'snapshot_date': 'datetime64[ns, UTC]',
        'sku': str,
        'total_onhand_qty': float,
        'total_inbound_qty': float,
        'reserved_distributable_qty': float,
        'available_distributable_qty': float 
    }

    awdDf = awdDf.astype(schema)

    return awdDf

def bsr (marketplace_action, access_token, asin_list):
    """
    This will pull BSR per marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - asin_list: list of asin

    return:
    - data frame of BSR Data in a marketplace
    """
    # API Pull
    rate_limiter = RateLimiter(tokens_per_second=2, capacity=2)
    records = []
    regionUrl, marketplace_id = marketplace_action()

    for asin in asin_list:
        url = regionUrl + f'/catalog/2022-04-01/items/{asin}'
        headers = {
                'x-amz-access-token': access_token
            }

        request_params  = {
            'marketplaceIds': marketplace_id,
            'includedData': 'salesRanks'
        }

        try:
            response =  rate_limiter.send_request(requests.get, url, headers=headers, params=request_params)
            if response.status_code == 200:
                records.extend([response.json()])
                print(f"Successfully fetched data for ASIN {asin}")
            else:
                print(f"Failed to fetch data for ASIN {asin}: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error fetching data for ASIN {asin}: {e}")


    # data frame
    bsrDf = []
    for record in records:
        if record.get('asin') is not None:
            data = {
                'asin': record.get('asin', np.nan),
            }

            displayGroup = record.get('salesRanks', [{}])[0].get('displayGroupRanks', [])
            if displayGroup:
                data['display_group'] = record.get('salesRanks', [{}])[0].get('displayGroupRanks', [{}])[0].get('title', np.nan)
                data['display_group_rank'] = record.get('salesRanks', [{}])[0].get('displayGroupRanks', [{}])[0].get('rank', np.nan)

            classifications = record.get('salesRanks', [{}])[0].get('classificationRanks', [])
            i = 1
            for classification in classifications:
                data[f'classification_id_{i}'] = record.get('salesRanks', [{}])[0].get('classificationRanks', [{}])[i-1].get('classificationId', np.nan)
                data[f'classification_title_{i}'] = record.get('salesRanks', [{}])[0].get('classificationRanks', [{}])[i-1].get('title', np.nan)
                data[f'classification_rank_{i}'] = record.get('salesRanks', [{}])[0].get('classificationRanks', [{}])[i-1].get('rank', np.nan)
                data[f'classification_link_{i}'] = record.get('salesRanks', [{}])[0].get('classificationRanks', [{}])[i-1].get('link', np.nan)
                i += 1

            bsrDf.append(data)

    bsrDf = pd.DataFrame(bsrDf)

    req_columns = [
        'asin',
        'display_group',
        'display_group_rank',
        'classification_id_1',
        'classification_title_1',
        'classification_rank_1',
        'classification_link_1',
        'classification_id_2',
        'classification_title_2',
        'classification_rank_2',
        'classification_link_2'
    ]

    for col in req_columns:
        if col not in bsrDf.columns:
            bsrDf[col] = np.nan

    bsrDf = bsrDf[req_columns]

    schema = {
        'asin': str,
        'display_group': str,
        'display_group_rank': float,
        'classification_id_1': str,
        'classification_title_1': str,
        'classification_rank_1': float,
        'classification_link_1': str,
        'classification_id_2': str,
        'classification_title_2': str,
        'classification_rank_2': float,
        'classification_link_2': str
    }

    bsrDf = bsrDf.astype(schema)

    return bsrDf

def browse_tree(marketplace_action, access_token, file_path_name, past_days, browse_node_id):
    """
    This will pull Browse Tree Data per marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name (This should be xml file)
    - past_days: number of days from today's date (UTC)
    - browse_node_id: the ID of the browse node in string format

    return:
    - data frame of FBA Manage Inventory Report
    """
    # Create Report
    regionUrl, marketplace_id = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    dataStartTime = (datetime.now(timezone.utc) - timedelta(days=past_days)).isoformat()

    request_params = {
        'marketplaceIds': [marketplace_id],
        'reportType': 'GET_XML_BROWSE_TREE_DATA',
        'dataStartTime': dataStartTime,
        'reportOptions': {
            'MarketplaceId': marketplace_id,
            'BrowseNodeId': browse_node_id
        }
    }

    create_response = requests.post(url, headers=headers, json=request_params,)
    report_id = create_response.json()['reportId']

    # Check Report Status
    endpoint = f'/reports/2021-06-30/reports/{report_id}'
    url = regionUrl + endpoint

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
        raise ValueError("Failed to get the report document:", document_response.json())

    # Data Frame
    browseNodeDf = pd.read_xml(file_path_name)
    browseNodeDf = browseNodeDf.drop_duplicates()
    browseNodeDf = browseNodeDf[browseNodeDf['browseNodeId'].notna()]
    browseNodeDf['browsePathByName']=browseNodeDf['browsePathByName'].replace({r',(?=\S)':'  >  '}, regex=True)

    req_columns = [
        'browseNodeId',
        'browseNodeName',
        'browseNodeStoreContextName',
        'browsePathById',
        'browsePathByName',
        'hasChildren',
        'productTypeDefinitions'
    ]

    for col in req_columns:
        if col not in browseNodeDf.columns:
            browseNodeDf[col] = np.nan

    browseNodeDf = browseNodeDf[req_columns]

    schema = {
        'browseNodeId': float,
        'browseNodeName': str,
        'browseNodeStoreContextName': str,
        'browsePathById': str,
        'browsePathByName': str,
        'hasChildren': str,
        'productTypeDefinitions': str
    }

    browseNodeDf = browseNodeDf.astype(schema)

    return browseNodeDf

def all_listing_report(marketplace_action, access_token, marketplace_code, file_path_name):
    """
    This will pull All Listing Report marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - marketplace_code: the code of the marketplace being pulled
    - file_path_name: the file path where to save the report up to its file name

    return:
    - data frame of All Listing Report
    """
    # Create Report
    print('Preparing for report request.')

    regionUrl, mid = marketplace_action()
    endpoint = f'/reports/2021-06-30/reports'
    url = regionUrl + endpoint
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }

    request_params = {
        'marketplaceIds': [mid],
        'reportType': 'GET_MERCHANT_LISTINGS_ALL_DATA'
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
        report_data = requests.get(download_url)

        with open(file_path_name, "wb") as f:
            f.write(report_data.content)
    else:
        print("Failed to get the report document:", document_response.json())

    # Data Frame
    try:
        allListingDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t')
    except:
        allListingDf = pd.read_csv(filepath_or_buffer=file_path_name, delimiter='\t', encoding='ISO-8859-1')

    allListingDf = allListingDf.rename(columns=lambda x:x.replace(' ','_').replace('-','_').lower())
    allListingDf.insert(0,'snapshot_date', datetime.now(timezone.utc).date())
    allListingDf['snapshot_date'] = pd.to_datetime(allListingDf['snapshot_date'])

    allListingDf.insert(1,'marketplace_code', marketplace_code)

    req_columns = [
        'snapshot_date',
        'marketplace_code',
        'item_name',
        'item_description',
        'listing_id',
        'seller_sku',
        'price',
        'quantity',
        'open_date',
        'image_url',
        'item_is_marketplace',
        'product_id_type',
        'zshop_shipping_fee',
        'item_note',
        'item_condition',
        'zshop_category1',
        'zshop_browse_path',
        'zshop_storefront_feature',
        'asin1',
        'asin2',
        'asin3',
        'will_ship_internationally',
        'expedited_shipping',
        'zshop_boldface',
        'product_id',
        'bid_for_featured_placement',
        'add_delete',
        'pending_quantity',
        'fulfillment_channel',
        'merchant_shipping_group',
        'status',
        'minimum_order_quantity',
        'sell_remainder'
    ]

    for col in req_columns:
        if col not in allListingDf.columns:
            allListingDf[col] = np.nan

    allListingDf = allListingDf[req_columns]

    schema = {
        'snapshot_date': 'datetime64[ns]',
        'marketplace_code': str,
        'item_name': str,
        'item_description': str,
        'listing_id': str,
        'seller_sku': str,
        'price': float,
        'quantity': float,
        'open_date': str,
        'image_url': str,
        'item_is_marketplace': str,
        'product_id_type': str,
        'zshop_shipping_fee': float,
        'item_note': str,
        'item_condition': float,
        'zshop_category1': str,
        'zshop_browse_path': str,
        'zshop_storefront_feature': str,
        'asin1': str,
        'asin2': str,
        'asin3': str,
        'will_ship_internationally': str,
        'expedited_shipping': str,
        'zshop_boldface': str,
        'product_id': str,
        'bid_for_featured_placement': str,
        'add_delete': str,
        'pending_quantity': float,
        'fulfillment_channel': str,
        'merchant_shipping_group': str,
        'status': str,
        'minimum_order_quantity': float,
        'sell_remainder': str
    }

    allListingDf = allListingDf.astype(schema)

    return allListingDf

def sqp_asin_report(
    marketplace_action,
    access_token,
    file_path_name,
    asins,
    reportPeriod,
    data_start_time,
    data_end_time
):
    """
    Generic function to request and download any Amazon SP-API report.
    
    Parameters:
    - marketplace_action: function that returns (regionUrl, marketplace_id)
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name
    - asins: space delimited string of ASINs to include in the report
    - reportPeriod: string indicating the report period ('WEEK', 'MONTH', 'QUARTER')
    - data_start_time: ISO 8601 datetime string for report start time
    - data_end_time: ISO 8601 datetime string for report end time
    
    Returns:
    - df: dataframe of the SQP ASIN Report
    """
    get_amz_report(
        marketplace_action,
        access_token,
        file_path_name,
        report_type='GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT',
        report_options={'asin': asins, 'reportPeriod': reportPeriod},
        data_start_time=data_start_time,
        data_end_time=data_end_time
    )

    # Read JSON file
    with open(file_path_name, 'r') as f:
        data = json.load(f)

    # Extract report specification for metadata
    report_spec = data['reportSpecification']

    # List to store flattened records
    records = []

    # Process each ASIN data entry
    for entry in data['dataByAsin']:
        # Create base record with common fields
        record = {
            # Date range
            'start_date': entry['startDate'],
            'end_date': entry['endDate'],
            'asin': entry['asin'],
            
            # Report metadata
            'report_period': report_spec['reportOptions']['reportPeriod'],
            'marketplace_id': report_spec['marketplaceIds'][0],
            
            # Search Query Data
            'search_query': entry['searchQueryData']['searchQuery'],
            'search_query_score': entry['searchQueryData']['searchQueryScore'],
            'search_query_volume': entry['searchQueryData']['searchQueryVolume'],
            
            # Impression Data
            'total_query_impression_count': entry['impressionData']['totalQueryImpressionCount'],
            'asin_impression_count': entry['impressionData']['asinImpressionCount'],
            'asin_impression_share': entry['impressionData']['asinImpressionShare'],
            
            # Click Data
            'total_click_count': entry['clickData']['totalClickCount'],
            'total_click_rate': entry['clickData']['totalClickRate'],
            'asin_click_count': entry['clickData']['asinClickCount'],
            'asin_click_share': entry['clickData']['asinClickShare'],
            'total_median_click_price_amount': entry['clickData']['totalMedianClickPrice']['amount'] if entry['clickData']['totalMedianClickPrice'] else None,
            'total_median_click_price_currency': entry['clickData']['totalMedianClickPrice']['currencyCode'] if entry['clickData']['totalMedianClickPrice'] else None,
            'asin_median_click_price_amount': entry['clickData']['asinMedianClickPrice']['amount'] if entry['clickData']['asinMedianClickPrice'] else None,
            'asin_median_click_price_currency': entry['clickData']['asinMedianClickPrice']['currencyCode'] if entry['clickData']['asinMedianClickPrice'] else None,
            'total_same_day_shipping_click_count': entry['clickData']['totalSameDayShippingClickCount'],
            'total_one_day_shipping_click_count': entry['clickData']['totalOneDayShippingClickCount'],
            'total_two_day_shipping_click_count': entry['clickData']['totalTwoDayShippingClickCount'],
            
            # Cart Add Data
            'total_cart_add_count': entry['cartAddData']['totalCartAddCount'],
            'total_cart_add_rate': entry['cartAddData']['totalCartAddRate'],
            'asin_cart_add_count': entry['cartAddData']['asinCartAddCount'],
            'asin_cart_add_share': entry['cartAddData']['asinCartAddShare'],
            'total_median_cart_add_price_amount': entry['cartAddData']['totalMedianCartAddPrice']['amount'] if entry['cartAddData']['totalMedianCartAddPrice'] else None,
            'total_median_cart_add_price_currency': entry['cartAddData']['totalMedianCartAddPrice']['currencyCode'] if entry['cartAddData']['totalMedianCartAddPrice'] else None,
            'asin_median_cart_add_price_amount': entry['cartAddData']['asinMedianCartAddPrice']['amount'] if entry['cartAddData']['asinMedianCartAddPrice'] else None,
            'asin_median_cart_add_price_currency': entry['cartAddData']['asinMedianCartAddPrice']['currencyCode'] if entry['cartAddData']['asinMedianCartAddPrice'] else None,
            'total_same_day_shipping_cart_add_count': entry['cartAddData']['totalSameDayShippingCartAddCount'],
            'total_one_day_shipping_cart_add_count': entry['cartAddData']['totalOneDayShippingCartAddCount'],
            'total_two_day_shipping_cart_add_count': entry['cartAddData']['totalTwoDayShippingCartAddCount'],
            
            # Purchase Data
            'total_purchase_count': entry['purchaseData']['totalPurchaseCount'],
            'total_purchase_rate': entry['purchaseData']['totalPurchaseRate'],
            'asin_purchase_count': entry['purchaseData']['asinPurchaseCount'],
            'asin_purchase_share': entry['purchaseData']['asinPurchaseShare'],
            'total_median_purchase_price_amount': entry['purchaseData']['totalMedianPurchasePrice']['amount'] if entry['purchaseData']['totalMedianPurchasePrice'] else None,
            'total_median_purchase_price_currency': entry['purchaseData']['totalMedianPurchasePrice']['currencyCode'] if entry['purchaseData']['totalMedianPurchasePrice'] else None,
            'asin_median_purchase_price_amount': entry['purchaseData']['asinMedianPurchasePrice']['amount'] if entry['purchaseData']['asinMedianPurchasePrice'] else None,
            'asin_median_purchase_price_currency': entry['purchaseData']['asinMedianPurchasePrice']['currencyCode'] if entry['purchaseData']['asinMedianPurchasePrice'] else None,
            'total_same_day_shipping_purchase_count': entry['purchaseData']['totalSameDayShippingPurchaseCount'],
            'total_one_day_shipping_purchase_count': entry['purchaseData']['totalOneDayShippingPurchaseCount'],
            'total_two_day_shipping_purchase_count': entry['purchaseData']['totalTwoDayShippingPurchaseCount'],
        }
        
        records.append(record)

    # Create DataFrame
    df = pd.DataFrame(records)

    safe_schema = {
        # Dates
        'start_date': 'datetime64[ns]',
        'end_date': 'datetime64[ns]',
        
        # Strings
        'asin': str,
        'report_period': str,
        'marketplace_id': str,
        'search_query': str,
        'total_median_click_price_currency': str,
        'asin_median_click_price_currency': str,
        'total_median_cart_add_price_currency': str,
        'asin_median_cart_add_price_currency': str,
        'total_median_purchase_price_currency': str,
        'asin_median_purchase_price_currency': str,
        
        # All numbers as float (handles nulls well)
        'search_query_score': float,
        'search_query_volume': float,
        'total_query_impression_count': float,
        'asin_impression_count': float,
        'asin_impression_share': float,
        'total_click_count': float,
        'total_click_rate': float,
        'asin_click_count': float,
        'asin_click_share': float,
        'total_median_click_price_amount': float,
        'asin_median_click_price_amount': float,
        'total_same_day_shipping_click_count': float,
        'total_one_day_shipping_click_count': float,
        'total_two_day_shipping_click_count': float,
        'total_cart_add_count': float,
        'total_cart_add_rate': float,
        'asin_cart_add_count': float,
        'asin_cart_add_share': float,
        'total_median_cart_add_price_amount': float,
        'asin_median_cart_add_price_amount': float,
        'total_same_day_shipping_cart_add_count': float,
        'total_one_day_shipping_cart_add_count': float,
        'total_two_day_shipping_cart_add_count': float,
        'total_purchase_count': float,
        'total_purchase_rate': float,
        'asin_purchase_count': float,
        'asin_purchase_share': float,
        'total_median_purchase_price_amount': float,
        'asin_median_purchase_price_amount': float,
        'total_same_day_shipping_purchase_count': float,
        'total_one_day_shipping_purchase_count': float,
        'total_two_day_shipping_purchase_count': float,
    }

    # Convert dates first
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])

    # Apply schema
    df = df.astype(safe_schema)
    
    return df

def multi_country_inv(
    marketplace_action,
    access_token,
    file_path_name
):
    """
    This will pull Multi-Country Inventory Report per region.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - file_path_name: the file path where to save the report up to its file name

    return:
    - data frame of Multi-Country Inventory Report
    """
    
    # get report
    get_amz_report(
        marketplace_action,
        access_token,
        file_path_name,
        report_type='GET_AFN_INVENTORY_DATA_BY_COUNTRY'
    )

    # Data Frame
    multiCountryInvDf = pd.read_csv(file_path_name, sep='\t')

    # Rename columns: replace '-' with '_'
    multiCountryInvDf.columns = multiCountryInvDf.columns.str.replace('-', '_')

    # Set data types for each column
    multiCountryInvDf = multiCountryInvDf.astype({
        'seller_sku': str,
        'fulfillment_channel_sku': str,
        'asin': str,
        'condition_type': str,
        'country': str,
        'quantity_for_local_fulfillment': float
    })

    # Insert date column as the first column
    multiCountryInvDf.insert(0, 'date', pd.to_datetime(datetime.now(timezone.utc).date()))

    return multiCountryInvDf

