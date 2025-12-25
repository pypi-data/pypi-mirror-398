import pandas as pd
import numpy as np
from datetime import datetime, timezone
import requests
import json
import time
import os

def _instacart_poll_report_status(report_id, access_token):
    url = f"https://api.ads.instacart.com/api/v3/reports/{report_id}"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    start_time = time.time()
    timeout_seconds = 3600  # 1 hour

    while True:
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError("Instacart report processing timed out after 1 hour.")

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to get Instacart report status: {response.status_code} - {response.text}")
            time.sleep(60)
            continue

        status = response.json()['data']['attributes']['status']
        print(f'Report Status: {status}')

        if status == 'completed':
            return True
        elif status in ('failed', 'cancelled'):
            raise ValueError(f"Instacart report generation failed with status: {status}")
        else:
            time.sleep(60)

def insta_api_get_refresh_token(client_id, client_secret, code):
    token_url = "https://api.ads.instacart.com/oauth/token"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": 'https://zvdataautomation.com/',
        "code": code,
        "grant_type": 'authorization_code',
    }

    response = requests.post(
        token_url,
        headers=headers,
        json=data,
    )

    try:
      refresh_token = response.json()['refresh_token']
      return refresh_token

    except requests.exceptions.RequestException as e:
      message = f"Error getting refresh token: {response.status_code} - {response.text}"
      raise ValueError(message)

def insta_api_get_access_token(client_id, client_secret, refresh_token):
    token_url = "https://api.ads.instacart.com/oauth/token"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": 'https://zvdataautomation.com/',
        "refresh_token": refresh_token,
        "grant_type": 'refresh_token',
    }

    response = requests.post(
        token_url,
        headers=headers,
        json=data,
    )

    try:
        access_token = response.json()['access_token']
        return access_token
    except requests.exceptions.RequestException as e:
        message = f"Error getting access token: {response.status_code} - {response.text}"
        raise ValueError(message)

def insta_api_get_product_report(start_date, end_date, file_path, access_token):
    # Request Report
    url = "https://api.ads.instacart.com/api/v3/charts/async/tables"

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }

    payload = {
        'source': 'sponsored_product_product',
        'query': {
            'date_range': {
                'start_date': start_date,
                'end_date': end_date,
            },
            'series': {
                'columns': [
                    'event.date',
                    'product.status',
                    'campaign.name',
                    'ad_group.name',
                    'product.name',
                    'product.size',
                    'product.scan_code',
                    'event.spend',
                    'event.attributed_sales_linear',
                    'event.attributed_units_linear',
                    'event.roas_linear',
                    'event.impressions',
                    'event.clicks',
                    'event.ctr',
                    'event.cpc',
                    'event.ntb_attributed_sales_linear',
                    'event.percent_ntb_sales_linear',
                    'product.id',
                    'campaign.id',
                    'ad_group.id'
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status() # Raise an exception for HTTP errors
        report_id = response.json()['data']['id']
        print(f'report_id: {report_id}')
    except requests.exceptions.RequestException as e:
        message = f"Error requesting Instacart product report: {response.status_code} - {response.text}"
        raise ValueError(message)

    # Check Report Status
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }

    fileReady = _instacart_poll_report_status(report_id, access_token)

    if not fileReady:
        raise ValueError("Instacart report generation failed or timed out.")
    
    # Download the report
    url = f"https://api.ads.instacart.com/api/v3/reports/{report_id}/download"
    response = requests.get(url, headers=headers)
    fileName = os.path.join(file_path, f'instacart_report_{report_id}.csv')
    with open(fileName, 'wb') as f:
        f.write(response.content)
    print('Report Downloaded')
    return fileName

def insta_ads_report(filePath:str):
    instaDf = pd.read_csv(filePath)

    # Rename columns from new Instacart format to existing format
    column_mapping = {
        'event.date': 'date',
        'product.status': 'status',
        'campaign.name': 'campaign',
        'ad_group.name': 'ad_group',
        'product.name': 'product',
        'product.size': 'product_size',
        'product.scan_code': 'upc',
        'event.spend': 'spend',
        'event.attributed_sales_linear': 'attributed_sales',
        'event.attributed_units_linear': 'attributed_quantities',
        'event.roas_linear': 'roas',
        'event.impressions': 'impressions',
        'event.clicks': 'clicks',
        'event.ctr': 'ctr',
        'event.cpc': 'average_cpc',
        'event.ntb_attributed_sales_linear': 'ntb_attributed_sales',
        'event.percent_ntb_sales_linear': 'percent_ntb_attributed_sales',
        'product.id': 'id',
        'campaign.id': 'campaign_uuid',
        'ad_group.id': 'ad_group_uuid'
    }

    instaDf = instaDf.rename(columns=column_mapping)
    instaDf['date'] = pd.to_datetime(instaDf['date'])

    req_columns = [
        'date',
        'status',
        'campaign',
        'ad_group',
        'product',
        'product_size',
        'upc',
        'spend',
        'attributed_sales',
        'attributed_quantities',
        'roas',
        'impressions',
        'clicks',
        'ctr',
        'average_cpc',
        'ntb_attributed_sales',
        'percent_ntb_attributed_sales',
        'id',
        'campaign_uuid',
        'ad_group_uuid'
    ]

    missingColumns = set(req_columns) - set(instaDf.columns)
    newColumns = set(instaDf.columns) - set(req_columns)

    if missingColumns:
        message = (
        f"""
        missing columns: {', '.join(missingColumns)}
        """
        )
        raise ValueError(message)
    if newColumns:
        message = (
        f"""
        new columns: {', '.join(newColumns)}
        """
        )
        print(message)


    instaDf = instaDf[req_columns]

    schema = {
        'date' : 'datetime64[ns]',
        'status' : str,
        'campaign' : str,
        'ad_group' : str,
        'product' : str,
        'product_size' : str,
        'upc' : str,
        'spend' : float,
        'attributed_sales' : float,
        'attributed_quantities' : float,
        'roas' : float,
        'impressions' : float,
        'clicks' : float,
        'ctr' : float,
        'average_cpc' : float,
        'ntb_attributed_sales' : float,
        'percent_ntb_attributed_sales' : float,
        'id' : str,
        'campaign_uuid' : str,
        'ad_group_uuid' : str
    }

    instaDf = instaDf.astype(schema)
    return instaDf

def insta_api_get_marketshare(access_token, start_date, end_date):
    url = 'https://api.ads.instacart.com/api/v3/charts/tables'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    payload = {
        "source": "sds",
        "query": {
            "series": {
                "columns": [
                    "sds.date",
                    "sds.brand_name",
                    "sds.category_name",
                    "sds.super_category_name",
                    "sds.department_name",
                    "sds.share",
                    "sds.brand_sales_usd",
                    "sds.brand_ad_spend_usd"
                ],
                "filters": [
                    {
                        "column": "sds.date",
                        "operation": "GTE",
                        "value": start_date
                    },
                    {
                        "column": "sds.date",
                        "operation": "LTE",
                        "value": end_date
                    },
                ],
                "order_bys": [
                    {
                        "column": "sds.date",
                        "direction": "DESC"
                    }
                ],
              "pagination": {
                  "page": 1,
                  "page_size": 500
              }
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status() # Raise an exception for HTTP errors
        columns_info = response.json()['data']['attributes']['header']['series']['columns']
        column_names = [col['name'].split('.')[-1] for col in columns_info]

        data_section = response.json()['data']['attributes']['data']['rows']
        shareDf = pd.DataFrame(data_section, columns=column_names)
    except requests.exceptions.RequestException as e:
        message = f"Error getting Instacart market share report: {response.status_code} - {response.text}"
        raise ValueError(message)

    req_columns = [
        'date',
        'brand_name',
        'category_name',
        'super_category_name',
        'department_name',
        'share',
        'brand_sales_usd',
        'brand_ad_spend_usd'
    ]

    missingColumns = set(req_columns) - set(shareDf.columns)
    newColumns = set(shareDf.columns) - set(req_columns)

    if missingColumns or newColumns:
        message = (
        f"""
        missing columns: {', '.join(missingColumns)}
        new columns: {', '.join(newColumns)}
        """
        )

        raise ValueError(message)

    shareDf = shareDf[req_columns]

    schema = {
        'date': 'datetime64[ns]',
        'brand_name': str,
        'category_name': str,
        'super_category_name': str,
        'department_name': str,
        'share': float,
        'brand_sales_usd': float,
        'brand_ad_spend_usd': float
        
    }
    
    shareDf = shareDf.astype(schema)
    return shareDf

