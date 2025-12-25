import pandas as pd
from .gmail_automation import gchat_space

def krogerAdReport (report_file):
    df = pd.read_csv(report_file)
    df = df.rename(columns=lambda x:x.replace(' ', '_').replace('(','').replace(')','').replace('-','_').lower())
    df['daily_date'] = pd.to_datetime(df['daily_date'])
    df['purchased_upc'] = df['purchased_upc'].fillna(0).astype(int).astype(str)
    df['product_id'] = df['product_id'].fillna(0).astype(int).astype(str)
    colRep = df.columns[11:]
    df[colRep] = df[colRep].replace({'\$': '', ',': '', '%':''}, regex=True)

    req_columns = [
        'campaign_name',
        'advertiser_id',
        'advertiser_name',
        'ad_group_name',
        'daily_date',
        'product_id',
        'product_name',
        'purchased_upc',
        'purchased_product',
        'campaign_status',
        'ad_group_status',
        'impressions',
        'clicks',
        'cost',
        'cost_per_click_cpc',
        'click_through_rate_ctr',
        'clicked_transactions',
        'clicked_units',
        'clicked_revenue',
        'clicked_roas',
        'viewed_units',
        'viewed_transactions',
        'viewed_revenue',
        'viewed_roas',
        'cost_per_thousand_cpm'
    ]

    missingColumns = set(req_columns) - set(df.columns)
    newColumns = set(df.columns) - set(req_columns)

    if missingColumns:
        message = (f"""\nMissing columns: {', '.join(missingColumns)}""")
        raise ValueError(message)
    if newColumns:
        message = (f"""\nKroger Manula Report New columns:\n {', '.join(newColumns)}""")
        gchat_space(message, 'https://chat.googleapis.com/v1/spaces/AAAAq774XOA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=2-eECUKfzs1-UsiN3-YG6IV-DzwrDSIoS-bKmqU2qZY')

    df = df[req_columns]

    schema = {
        'campaign_name': str,
        'advertiser_id': str,
        'advertiser_name': str,
        'ad_group_name': str,
        'daily_date': 'datetime64[ns]',
        'product_id': str,
        'product_name': str,
        'purchased_upc': str,
        'purchased_product': str,
        'campaign_status': str,
        'ad_group_status': str,
        'impressions': float,
        'clicks': float,
        'cost': float,
        'cost_per_click_cpc': float,
        'click_through_rate_ctr': float,
        'clicked_transactions': float,
        'clicked_units': float,
        'clicked_revenue': float,
        'clicked_roas': float,
        'viewed_units': float,
        'viewed_transactions': float,
        'viewed_revenue': float,
        'viewed_roas': float,
        'cost_per_thousand_cpm': float
    }
    df = df.astype(schema)

    return df

