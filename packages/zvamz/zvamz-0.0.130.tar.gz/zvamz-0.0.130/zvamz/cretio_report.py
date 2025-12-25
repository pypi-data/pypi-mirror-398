import os
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import pytz
import requests
import json
import time
import http.client

def _criteo_poll_report_status(report_id, version, access_token):
    url = f"https://api.criteo.com/{version}/retail-media/reports/{report_id}/status"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    start_time = time.time()
    timeout_seconds = 3600  # 1 hour

    while True:
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError("Criteo report processing timed out after 1 hour.")

        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to get Criteo report status: {response.status_code} - {response.text}")
            time.sleep(60)
            continue

        status = response.json()['data']['attributes']['status']
        print(f"Criteo report status: {status}")

        if status == 'success':
            return True
        elif status in ('failed', 'cancelled'):
            raise ValueError(f"Criteo report generation failed with status: {status}")
        else:
            time.sleep(20)

def cretio_get_access_token(grant_type, client_id, client_secret):
    url = "https://api.criteo.com/oauth2/token"

    payload = {
        "grant_type": grant_type,
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded"
    }

    response = requests.post(url, data=payload, headers=headers)

    try:
        access_token = response.json()['access_token']
        print(f'Access Token: {access_token}')
        return access_token
    except Exception as e:
        raise ValueError(f'{response.status_code} - {response.text}')

def criteo_campaign_report(access_token, version, report_type, ids, start_date, end_date, file_path_name):
    #create report
    url = f"https://api.criteo.com/{version}/retail-media/reports/campaigns"

    payload = json.dumps({
      "data": {
        "attributes": {
          "endDate": end_date,
          "startDate": start_date,
          "timezone": "EST",
          "salesChannel": "all",
          "campaignType": "all",
          "clickAttributionWindow": "none",
          "viewAttributionWindow": "none",
          "format": "csv",
          # "id": "619284442499084288",
          "ids": ids,
          "reportType": report_type,
          # "dimensions": [],
          # "metrics": [],
          # "searchTermTargetings": [,
          # "searchTermTypes": [],
        },
        # "type": "<string>"
      }
    })
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        report_id = response.json()['data']['id']
        print(report_id)
    except requests.exceptions.RequestException as e:
        print(f"Error creating Criteo report: {e}")
        raise ValueError(f'{response.status_code} - {response.text}')

    # check status
    url = f"https://api.criteo.com/{version}/retail-media/reports/{report_id}/status"

    payload={}
    headers = {
      'Accept': 'application/json',
      'Authorization': f'Bearer {access_token}'
    }

    _criteo_poll_report_status(report_id, version, access_token)

    # download file
    url = f"https://api.criteo.com/{version}/retail-media/reports/{report_id}/output"

    payload={}
    headers = {
      'Accept': 'application/octet-stream',
      'Authorization': f'Bearer {access_token}'
    }

    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        with open(file_path_name, 'wb') as f:
            f.write(response.content)
        print("Report saved!")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading Criteo report: {e}")
        raise ValueError(f'{response.status_code} - {response.text}')

