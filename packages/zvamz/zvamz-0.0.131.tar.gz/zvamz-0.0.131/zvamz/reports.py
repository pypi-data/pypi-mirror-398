import pandas as pd
import numpy as np
from datetime import datetime, timezone
from .fc_address import fc_address_list


def bgdeldup(dateName:str, minDate: datetime, client: str, bgTable:str):
    """
    Delete the data from the declared minDate to avoid duplicate in the database

    Parameters:
    - dateName: the name of the date column
    - minDate: the start date that will be deleted to avoid duplicate
    - client: the BigQuery client name
    - bgTable: the BigQuery Table address

    Returns:
    - delete the data to avoid duplicate
    """
    delDataQuery = f"""
    DELETE FROM
    `{bgTable}`
    WHERE
    {dateName} >= '{minDate}'
    """

    delData = client.query(delDataQuery)
    delData = delData.result()

    return delData

def bgdeldupM(dateName:str, minDate: datetime, marketplaceName:str, marketplacesArray,  client: str, bgTable:str):
    marketplaces_str = ", ".join(f"'{marketplace}'" for marketplace in marketplacesArray)

    delDataQuery = f"""
    DELETE FROM
        `{bgTable}`
    WHERE
        {dateName} >= '{minDate}'
        AND {marketplaceName} IN ({marketplaces_str})
    """

    delData = client.query(delDataQuery)
    delData = delData.result()

    return delData

def bgdeldupf(dateName:str, minDate: datetime, client: str, bgTable:str):
    """
    Delete the data from the declared minDate to avoid duplicate in the database
    (free version of BigQuery)

    Parameters:
    - dateName: the name of the date column
    - minDate: the start date that will be deleted to avoid duplicate
    - client: the BigQuery client name
    - bgTable: the BigQuery Table address

    Returns:
    - delete the data to avoid duplicate
    """
    delDataQuery = f"""
    CREATE OR REPLACE TABLE `{bgTable}` AS

    SELECT *
    FROM `{bgTable}`
    WHERE
    {dateName} < '{minDate}'
    """

    delData = client.query(delDataQuery)
    delData = delData.result()

    return delData

def bgdeldupfM(dateName:str, minDate: datetime, marketplaceName:str, marketplacesArray,  client: str, bgTable:str):
    marketplaces_str = ", ".join(f"'{marketplace}'" for marketplace in marketplacesArray)

    delDataQuery = f"""
    CREATE OR REPLACE TABLE `{bgTable}` AS

    SELECT *
    FROM `{bgTable}`
    WHERE NOT(
        {dateName} >= '{minDate}'
        AND IFNULL({marketplaceName}, 'nan') IN ({marketplaces_str})
    )
    """

    delData = client.query(delDataQuery)
    delData = delData.result()

    return delData

def dfbgcolcheck(df: pd.DataFrame, client: str, bgTable: str):
    """
    This function compares the columns of DataFrame and existing BigQuery Table

    Paremeters:
    - df: Data frame to check
    - client: name of BigQuery client
    - bgTable: the address of BigQuery Table

    Returns:
    - True if it matches
    - ValueError if not
    """
    existingDataQuery = f"""
    SELECT
    *
    FROM
    `{bgTable}`
    LIMIT 10
    """

    existingData = client.query(existingDataQuery).to_dataframe()

    columnsCheck = existingData.columns.equals(df.columns)
    if columnsCheck:
        print("Column names and positions are the same.")
        return True
    else:
        missingColumns = set(existingData.columns) - set(df.columns)
        newColumns = set(df.columns) - set(existingData.columns)

        message = (
        f"""
        Column names and positions are not the same.
        missing columns: {', '.join(missingColumns)}
        new columns: {', '.join(newColumns)}
        """
        )
            
        raise ValueError(message)

def lowfeereport(filePath:str):
    """
    This function process and clean the Amazon Economics Report.
    It extracts the low level inventory data

    Paremeters:
    - filePath: the path where the report is saved

    Returns:
    - DataFrame of the cleaned report
    - Flase if there is no data related to low level inventory fee
    """
    lowFeeDf = pd.read_csv(filePath)

    checkCol = [
        'Low-inventory-level fee per unit',
        'Low-inventory-level fee quantity',
        'Low-inventory-level fee total'
    ]

    colCheck = all(col in lowFeeDf.columns for col in checkCol)

    if colCheck:
        lowFeeDf = lowFeeDf[[
            'Start date',
            'End date',
            'ASIN',
            'MSKU',
            'Low-inventory-level fee per unit',
            'Low-inventory-level fee quantity',
            'Low-inventory-level fee total'
        ]]

        lowFeeDf = lowFeeDf.rename(columns=lambda x:x.replace('-','_').replace(' ','_').lower())
        lowFeeDf['start_date'] = pd.to_datetime(lowFeeDf['start_date'])
        lowFeeDf['end_date'] = pd.to_datetime(lowFeeDf['end_date'])

        schema = {
                'start_date': 'datetime64[ns]',
                'end_date': 'datetime64[ns]',
                'asin': str,
                'msku': str,
                'low_inventory_level_fee_per_unit': float,
                'low_inventory_level_fee_quantity': float,
                'low_inventory_level_fee_total': float
        }

        lowFeeDf = lowFeeDf.astype(schema)
        return lowFeeDf
    else:
        return False
    
def promoreport(filePath:str):
    """
    Clean the raw file downloaded in Amazon Seller Central Promotions Report

    Parameter:
    - filePath: the path where the downloaded Promotions Report is located

    Return:
    - DataFrame of the cleaned report
    """
    promoDf = pd.read_csv(filePath)
    promoDf = promoDf.rename(columns=lambda x:x.replace('?','').replace('"','').replace('-','_').lower())
    promoDf['shipment_date'] = pd.to_datetime(promoDf['shipment_date'], utc=True)

    schema = {
        'shipment_date': 'datetime64[ns, UTC]',
        'currency': str,
        'item_promotion_discount': float,
        'item_promotion_id': str,
        'description': str,
        'promotion_rule_value': str,
        'amazon_order_id': str,
        'shipment_id': str,
        'shipment_item_id': str
    }
    promoDf = promoDf.astype(schema)

    return promoDf

def spstreport(filePath:str, marketplace:str):
    spSearchTermDf = pd.read_excel(filePath)
    spSearchTermDf = spSearchTermDf.rename(columns=lambda X:X.replace('7','_7').replace('-','').replace('#','').replace('(','').replace(')','').replace(' ','_').lower())

    reqColumns = [
        'marketplace',
        'date',
        'portfolio_name',
        'currency',
        'campaign_name',
        'ad_group_name',
        'targeting',
        'match_type',
        'customer_search_term',
        'impressions',
        'clicks',
        'clickthru_rate_ctr',
        'cost_per_click_cpc',
        'spend',
        '_7_day_total_sales_',
        'total_advertising_cost_of_sales_acos_',
        'total_return_on_advertising_spend_roas',
        '_7_day_total_orders_',
        '_7_day_total_units_',
        '_7_day_conversion_rate',
        '_7_day_advertised_sku_units_',
        '_7_day_other_sku_units_',
        '_7_day_advertised_sku_sales_',
        '_7_day_other_sku_sales_',
        'retailer'
    ]

    spSearchTermDf.insert(0,'marketplace',marketplace)

    addColumns = [
        'retailer'
    ]

    for col in addColumns:
        if col not in spSearchTermDf:
            spSearchTermDf[col] = np.nan

    missingColumns = set(reqColumns) - set(spSearchTermDf.columns)
    newColumns = set(spSearchTermDf.columns) - set(reqColumns)

    if missingColumns:
        message = f"Missing columns: {', '.join(missingColumns)}"
        raise ValueError(message)

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    spSearchTermDf = spSearchTermDf[reqColumns]

    schema = {
        'marketplace': str,
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'currency': str,
        'campaign_name': str,
        'ad_group_name': str,
        'targeting': str,
        'match_type': str,
        'customer_search_term': str,
        'impressions': float,
        'clicks': float,
        'clickthru_rate_ctr': float,
        'cost_per_click_cpc': float,
        'spend': float,
        '_7_day_total_sales_': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_7_day_total_orders_': float,
        '_7_day_total_units_': float,
        '_7_day_conversion_rate': float,
        '_7_day_advertised_sku_units_': float,
        '_7_day_other_sku_units_': float,
        '_7_day_advertised_sku_sales_': float,
        '_7_day_other_sku_sales_': float,
        'retailer': str
    }

    spSearchTermDf = spSearchTermDf.astype(schema)

    return spSearchTermDf

def sbstreport(filePath:str, marketplace:str):
    sbSearchTermDf = pd.read_excel(filePath)
    sbSearchTermDf = sbSearchTermDf.rename(columns=lambda X:X.replace('14','_14').replace('-','').replace('#','').replace('(','').replace(')','').replace(',','').replace(' ','_').lower())
    sbSearchTermDf.insert(0,'marketplace',marketplace)
    
    reqColumns = [
        'marketplace',
        'date',
        'portfolio_name',
        'currency',
        'campaign_name',
        'ad_group_name',
        'targeting',
        'match_type',
        'customer_search_term',
        'cost_type',
        'impressions',
        'viewable_impressions',
        'clicks',
        'clickthru_rate_ctr',
        'spend',
        'cost_per_click_cpc',
        'cost_per_1000_viewable_impressions_vcpm',
        'total_advertising_cost_of_sales_acos_',
        'total_return_on_advertising_spend_roas',
        '_14_day_total_sales_',
        '_14_day_total_orders_',
        '_14_day_total_units_',
        '_14_day_conversion_rate',
        'total_advertising_cost_of_sales_acos__click',
        'total_return_on_advertising_spend_roas__click',
        '_14_day_total_sales__click',
        '_14_day_total_orders___click',
        '_14_day_total_units___click'
    ]

    missingColumns = set(reqColumns) - set(sbSearchTermDf.columns)
    newColumns = set(sbSearchTermDf.columns) - set(reqColumns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    sbSearchTermDf = sbSearchTermDf[reqColumns]

    schema = {
        'marketplace': str,
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'currency': str,
        'campaign_name': str,
        'ad_group_name': str,
        'targeting': str,
        'match_type': str,
        'customer_search_term': str,
        'cost_type': str,
        'impressions': float,
        'viewable_impressions': float,
        'clicks': float,
        'clickthru_rate_ctr': float,
        'spend': float,
        'cost_per_click_cpc': float,
        'cost_per_1000_viewable_impressions_vcpm': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_14_day_total_sales_': float,
        '_14_day_total_orders_': float,
        '_14_day_total_units_': float,
        '_14_day_conversion_rate': float,
        'total_advertising_cost_of_sales_acos__click': float,
        'total_return_on_advertising_spend_roas__click': float,
        '_14_day_total_sales__click': float,
        '_14_day_total_orders___click': float,
        '_14_day_total_units___click': float
    }

    sbSearchTermDf = sbSearchTermDf.astype(schema)

    return sbSearchTermDf

def sdtreport(filePath:str, marketplace:str):
    sdTargetingDf = pd.read_excel(filePath)
    sdTargetingDf = sdTargetingDf.rename(columns=lambda X:X.replace('14','_14').replace('-','').replace('#','').replace('(','').replace(')','').replace(',','').replace(' ','_').lower())

    sdTargetingDf.insert(0,'marketplace',marketplace)

    reqColumns = [
        'marketplace',
        'date',
        'currency',
        'campaign_name',
        'portfolio_name',
        'cost_type',
        'ad_group_name',
        'targeting',
        'bid_optimization',
        'impressions',
        'viewable_impressions',
        'clicks',
        'clickthru_rate_ctr',
        '_14_day_detail_page_views_dpv',
        'spend',
        'cost_per_click_cpc',
        'cost_per_1000_viewable_impressions_vcpm',
        'total_advertising_cost_of_sales_acos_',
        'total_return_on_advertising_spend_roas',
        '_14_day_total_orders_',
        '_14_day_total_units_',
        '_14_day_total_sales_',
        '_14_day_newtobrand_orders_',
        '_14_day_newtobrand_sales',
        '_14_day_newtobrand_units_',
        'total_advertising_cost_of_sales_acos__click',
        'total_return_on_advertising_spend_roas__click',
        '_14_day_total_orders___click',
        '_14_day_total_units___click',
        '_14_day_total_sales__click',
        '_14_day_newtobrand_orders___click',
        '_14_day_newtobrand_sales__click',
        '_14_day_newtobrand_units___click'
    ]

    missingColumns = set(reqColumns) - set(sdTargetingDf.columns)
    newColumns = set(sdTargetingDf.columns) - set(reqColumns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    sdTargetingDf = sdTargetingDf[reqColumns]

    schema = {
        'date': 'datetime64[ns]',
        'currency': str,
        'campaign_name': str,
        'portfolio_name': str,
        'cost_type': str,
        'ad_group_name': str,
        'targeting': str,
        'bid_optimization': str,
        'impressions': float,
        'viewable_impressions': float,
        'clicks': float,
        'clickthru_rate_ctr': float,
        '_14_day_detail_page_views_dpv': float,
        'spend': float,
        'cost_per_click_cpc': float,
        'cost_per_1000_viewable_impressions_vcpm': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_14_day_total_orders_': float,
        '_14_day_total_units_': float,
        '_14_day_total_sales_': float,
        '_14_day_newtobrand_orders_': float,
        '_14_day_newtobrand_sales': float,
        '_14_day_newtobrand_units_': float,
        'total_advertising_cost_of_sales_acos__click': float,
        'total_return_on_advertising_spend_roas__click': float,
        '_14_day_total_orders___click': float,
        '_14_day_total_units___click': float,
        '_14_day_total_sales__click': float,
        '_14_day_newtobrand_orders___click': float,
        '_14_day_newtobrand_sales__click': float,
        '_14_day_newtobrand_units___click': float
    }

    sdTargetingDf = sdTargetingDf.astype(schema)

    return sdTargetingDf

def spcreport(filePath:str):
    spCampaignDf = pd.read_csv(filePath)
    spCampaignDf = spCampaignDf.rename(columns=lambda X:X.replace('7','_7').replace('-','').replace('#','').replace('(','').replace(')','').replace(',','').replace(' ','_').lower())

    colRange = spCampaignDf.columns[7:]
    spCampaignDf[colRange] = spCampaignDf[colRange].replace({'%':'','\$':'',',':''}, regex=True)
    spCampaignDf['date'] = pd.to_datetime(spCampaignDf['date'])

    schema = {
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'campaign_type': str,
        'campaign_name': str,
        'country': str,
        'status': str,
        'currency': str,
        'budget': float,
        'targeting_type': str,
        'bidding_strategy': str,
        'impressions': float,
        'last_year_impressions': float,
        'clicks': float,
        'last_year_clicks': float,
        'clickthru_rate_ctr': float,
        'spend': float,
        'last_year_spend': float,
        'cost_per_click_cpc': float,
        'last_year_cost_per_click_cpc': float,
        '_7_day_total_orders_': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_7_day_total_sales_': float
    }

    spCampaignDf = spCampaignDf.astype(schema)

    return spCampaignDf

def sbcreport(filePath:str):
    sbCampaignDf = pd.read_excel(filePath)
    sbCampaignDf = sbCampaignDf.rename(columns=lambda X:X.replace('14','_14').replace('5','_5').replace('-','').replace('#','').replace('(','').replace(')','').replace(',','').replace(' ','_').lower())

    colRange = sbCampaignDf.columns[6:]
    sbCampaignDf[colRange] = sbCampaignDf[colRange].replace({'%':'','\$':'',',':''}, regex=True)
    sbCampaignDf['date'] = pd.to_datetime(sbCampaignDf['date'])

    schema = {
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'currency': str,
        'campaign_name': str,
        'cost_type': str,
        'country': str,
        'impressions': float,
        'clicks': float,
        'clickthru_rate_ctr': float,
        'cost_per_click_cpc': float,
        'spend': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_14_day_total_sales_': float,
        '_14_day_total_orders_': float,
        '_14_day_total_units_': float,
        '_14_day_conversion_rate': float,
        'viewable_impressions': float,
        'cost_per_1000_viewable_impressions_vcpm': float,
        'viewthrough_rate_vtr': float,
        'clickthrough_rate_for_views_vctr': float,
        'video_first_quartile_views': float,
        'video_midpoint_views': float,
        'video_third_quartile_views': float,
        'video_complete_views': float,
        'video_unmutes': float,
        '_5_second_views': float,
        '_5_second_view_rate': float,
        '_14_day_branded_searches': float,
        '_14_day_detail_page_views_dpv': float,
        '_14_day_newtobrand_orders_': float,
        '_14_day_%_of_orders_newtobrand': float,
        '_14_day_newtobrand_sales': float,
        '_14_day_%_of_sales_newtobrand': float,
        '_14_day_newtobrand_units_': float,
        '_14_day_%_of_units_newtobrand': float,
        '_14_day_newtobrand_order_rate': float,
        'total_advertising_cost_of_sales_acos__click': float,
        'total_return_on_advertising_spend_roas__click': float,
        '_14_day_total_sales__click': float,
        '_14_day_total_orders___click': float,
        '_14_day_total_units___click': float,
        'newtobrand_detail_page_views': float,
        'newtobrand_detail_page_view_clickthrough_conversions': float,
        'newtobrand_detail_page_view_rate': float,
        'effective_cost_per_newtobrand_detail_page_view': float,
        '_14_day_atc': float,
        '_14_day_atc_clicks': float,
        '_14_day_atcr': float,
        'effective_cost_per_add_to_cart_ecpatc': float,
        'branded_searches_clickthrough_conversions': float,
        'branded_searches_rate': float,
        'effective_cost_per_branded_search': float
    }

    sbCampaignDf = sbCampaignDf.astype(schema)
    
    return sbCampaignDf

def sdcreport(filePath:str):
    sdCampaignDf = pd.read_excel(filePath)
    sdCampaignDf = sdCampaignDf.rename(columns=lambda X:X.replace('14','_14').replace('-','').replace('#','').replace('(','').replace(')','').replace(',','').replace(' ','_').lower())

    colRange = sdCampaignDf.columns[4:]
    sdCampaignDf[colRange] = sdCampaignDf[colRange].replace({'%':'','\$':'',',':''}, regex=True)
    sdCampaignDf['date'] = pd.to_datetime(sdCampaignDf['date'])

    schema = {
        'date': 'datetime64[ns]',
        'country': str,
        'status': str,
        'currency': str,
        'budget': float,
        'campaign_name': str,
        'portfolio_name': str,
        'cost_type': str,
        'impressions': float,
        'viewable_impressions': float,
        'clicks': float,
        'clickthru_rate_ctr': float,
        '_14_day_detail_page_views_dpv': float,
        'spend': float,
        'cost_per_click_cpc': float,
        'cost_per_1000_viewable_impressions_vcpm': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_14_day_total_orders_': float,
        '_14_day_total_units_': float,
        '_14_day_total_sales_': float,
        '_14_day_newtobrand_orders_': float,
        '_14_day_newtobrand_sales': float,
        '_14_day_newtobrand_units_': float,
        'total_advertising_cost_of_sales_acos__click': float,
        'total_return_on_advertising_spend_roas__click': float,
        '_14_day_total_orders___click': float,
        '_14_day_total_units___click': float,
        '_14_day_total_sales__click': float,
        '_14_day_newtobrand_orders___click': float,
        '_14_day_newtobrand_sales__click': float,
        '_14_day_newtobrand_units___click': float,
        'newtobrand_detail_page_views': float,
        'newtobrand_detail_page_view_viewthrough_conversions': float,
        'newtobrand_detail_page_view_clickthrough_conversions': float,
        'newtobrand_detail_page_view_rate': float,
        'effective_cost_per_newtobrand_detail_page_view': float,
        '_14_day_atc': float,
        '_14_day_atc_views': float,
        '_14_day_atc_clicks': float,
        '_14_day_atcr': float,
        'effective_cost_per_add_to_cart_ecpatc': float,
        '_14_day_branded_searches': float,
        'branded_searches_viewthrough_conversions': float,
        'branded_searches_clickthrough_conversions': float,
        'branded_searches_rate': float,
        'effective_cost_per_branded_search': float
    }

    sdCampaignDf = sdCampaignDf.astype(schema)

    return sdCampaignDf

def unifiedRepo(filePath:str):
    unifiedDf = pd.read_csv(filePath, skiprows=7)
    unifiedDf = unifiedDf.rename(columns=lambda x:x.replace(' ','_').replace('-','_').replace('(','').replace(')','').replace('/','_'))

    unifiedDf['quantity'] = unifiedDf['quantity'].replace({np.nan:0},regex=True)
    colmChange = unifiedDf.columns[14:]
    unifiedDf[colmChange] = unifiedDf[colmChange].replace({',':''},regex=True)

    unifiedDf['date_time'] = pd.to_datetime(unifiedDf['date_time'].replace({' PDT':'', ' PST':''}, regex=True))
    unifiedDf['date_time'] = unifiedDf['date_time'].dt.tz_localize('America/Los_Angeles', ambiguous=True)

    req_columns = [
        'date_time',
        'settlement_id',
        'type',
        'order_id',
        'sku',
        'description',
        'quantity',
        'marketplace',
        'account_type',
        'fulfillment',
        'order_city',
        'order_state',
        'order_postal',
        'tax_collection_model',
        'product_sales',
        'product_sales_tax',
        'shipping_credits',
        'shipping_credits_tax',
        'gift_wrap_credits',
        'giftwrap_credits_tax',
        'Regulatory_Fee',
        'Tax_On_Regulatory_Fee',
        'promotional_rebates',
        'promotional_rebates_tax',
        'marketplace_withheld_tax',
        'selling_fees',
        'fba_fees',
        'other_transaction_fees',
        'other',
        'total'    
    ]

    for col in req_columns:
        if col not in unifiedDf.columns:
            unifiedDf[col] = np.nan

    unifiedDf = unifiedDf[req_columns]

    schema = {
        'date_time': 'datetime64[ns, America/Los_Angeles]',
        'settlement_id': str,
        'type': str,
        'order_id': str,
        'sku': str,
        'description': str,
        'quantity': int,
        'marketplace': str,
        'account_type': str,
        'fulfillment': str,
        'order_city': str,
        'order_state': str,
        'order_postal': str,
        'tax_collection_model': str,
        'product_sales': float,
        'product_sales_tax': float,
        'shipping_credits': float,
        'shipping_credits_tax': float,
        'gift_wrap_credits': float,
        'giftwrap_credits_tax': float,
        'Regulatory_Fee': float,
        'Tax_On_Regulatory_Fee': float,
        'promotional_rebates': float,
        'promotional_rebates_tax': float,
        'marketplace_withheld_tax': float,
        'selling_fees': float,
        'fba_fees': float,
        'other_transaction_fees': float,
        'other': float,
        'total': float
    }

    unifiedDf = unifiedDf.astype(schema)

    return unifiedDf

def storageFeeReport(filePath:str):
    try:
        storageFeeDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        storageFeeDf = pd.read_csv(filePath, encoding='ISO-8859-1')

    storageFeeDf['month_of_charge'] = pd.to_datetime(storageFeeDf['month_of_charge'])

    req_columns = [
        'asin',
        'fnsku',
        'product_name',
        'fulfillment_center',
        'country_code',
        'longest_side',
        'median_side',
        'shortest_side',
        'measurement_units',
        'weight',
        'weight_units',
        'item_volume',
        'volume_units',
        'product_size_tier',
        'average_quantity_on_hand',
        'average_quantity_pending_removal',
        'estimated_total_item_volume',
        'month_of_charge',
        'storage_utilization_ratio',
        'storage_utilization_ratio_units',
        'base_rate',
        'utilization_surcharge_rate',
        'avg_qty_for_sus',
        'est_vol_for_sus',
        'est_base_msf',
        'est_sus',
        'currency',
        'estimated_monthly_storage_fee',
        'dangerous_goods_storage_type',
        'eligible_for_inventory_discount',
        'qualifies_for_inventory_discount',
        'total_incentive_fee_amount',
        'breakdown_incentive_fee_amount',
        'average_quantity_customer_orders'
    ]

    for col in req_columns:
        if col not in storageFeeDf.columns:
            storageFeeDf[col] = np.nan

    storageFeeDf = storageFeeDf[req_columns]

    schema = {
        'asin': str,
        'fnsku': str,
        'product_name': str,
        'fulfillment_center': str,
        'country_code': str,
        'longest_side': float,
        'median_side': float,
        'shortest_side': float,
        'measurement_units': str,
        'weight': float,
        'weight_units': str,
        'item_volume': float,
        'volume_units': str,
        'product_size_tier': str,
        'average_quantity_on_hand': float,
        'average_quantity_pending_removal': float,
        'estimated_total_item_volume': float,
        'month_of_charge': 'datetime64[ns]',
        'storage_utilization_ratio': str,
        'storage_utilization_ratio_units': str,
        'base_rate': float,
        'utilization_surcharge_rate': float,
        'avg_qty_for_sus': float,
        'est_vol_for_sus': float,
        'est_base_msf': float,
        'est_sus': float,
        'currency': str,
        'estimated_monthly_storage_fee': float,
        'dangerous_goods_storage_type': str,
        'eligible_for_inventory_discount': str,
        'qualifies_for_inventory_discount': str,
        'total_incentive_fee_amount': float,
        'breakdown_incentive_fee_amount': str,
        'average_quantity_customer_orders': float
    }
    storageFeeDf = storageFeeDf.astype(schema)

    return storageFeeDf

def overAgeFeeReport(filepath:str):
    try:
        overAgeDf = pd.read_csv(filepath)
    except UnicodeDecodeError:
        overAgeDf = pd.read_csv(filepath, encoding='ISO-8859-1')

    overAgeDf = overAgeDf.rename(columns=lambda x:x.replace('-','_').lower())

    overAgeDf['snapshot_date'] = pd.to_datetime(overAgeDf['snapshot_date'])

    req_columns = [
        'snapshot_date',
        'sku',
        'fnsku',
        'asin',
        'product_name',
        'condition',
        'per_unit_volume',
        'currency',
        'volume_unit',
        'country',
        'qty_charged',
        'amount_charged',
        'surcharge_age_tier',
        'rate_surcharge'
    ]

    for col in req_columns:
        if col not in overAgeDf.columns:
            overAgeDf[col] = np.nan

    overAgeDf = overAgeDf[req_columns]

    schema = {
        'snapshot_date': 'datetime64[ns, UTC]',
        'sku': str,
        'fnsku': str,
        'asin': str,
        'product_name': str,
        'condition': str,
        'per_unit_volume': float,
        'currency': str,
        'volume_unit': str,
        'country': str,
        'qty_charged': float,
        'amount_charged': float,
        'surcharge_age_tier': str,
        'rate_surcharge': float
    }

    overAgeDf = overAgeDf.astype(schema)

    return overAgeDf

def returnProcessFeeReport(filepath:str):
    try:
        returnFeeDf = pd.read_csv(filepath)
    except UnicodeDecodeError:
        returnFeeDf = pd.read_csv(filepath, encoding='ISO-8859-1')

    returnFeeDf['month_of_charge'] = pd.to_datetime(returnFeeDf['month_of_charge'])
    returnFeeDf['month_of_shipment'] = pd.to_datetime(returnFeeDf['month_of_shipment'])

    req_columns = [
        'asin',
        'asin_fee_category',
        'fnsku',
        'product_name',
        'longest_side',
        'median_side',
        'shortest_side',
        'measurement-units',
        'unit_weight',
        'dimensional_weight',
        'shipping_weight',
        'weight_units',
        'sku_sizetier',
        'month_of_shipment',
        'asin_shipped_units',
        'asin_return_threshold_percent',
        'asin_return_threshold_units',
        'asin_returned_units',
        'sku_returned_units_NSP_exempted',
        'sku_returned_units_charged',
        'sku_fee_per_unit',
        'sku_returns_fee',
        'month_of_charge',
        'currency'
    ]

    for col in req_columns:
        if col not in returnFeeDf.columns:
            returnFeeDf[col] = np.nan

    returnFeeDf = returnFeeDf[req_columns]

    schema = {
        'asin': str,
        'asin_fee_category': str,
        'fnsku': str,
        'product_name': str,
        'longest_side': float,
        'median_side': float,
        'shortest_side': float,
        'measurement-units': str,
        'unit_weight': float,
        'dimensional_weight': float,
        'shipping_weight': float,
        'weight_units': str,
        'sku_sizetier': str,
        'month_of_shipment': 'datetime64[ns]',
        'asin_shipped_units': float,
        'asin_return_threshold_percent': float,
        'asin_return_threshold_units': float,
        'asin_returned_units': float,
        'sku_returned_units_NSP_exempted': float,
        'sku_returned_units_charged': float,
        'sku_fee_per_unit': float,
        'sku_returns_fee': float,
        'month_of_charge': 'datetime64[ns]',
        'currency': str
    }

    returnFeeDf = returnFeeDf.astype(schema)

    return returnFeeDf

def fbaFeeReport(filePath:str):
    try:
        fbaFeeDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        fbaFeeDf = pd.read_csv(filePath, encoding='ISO-8859-1')

    fbaFeeDf = fbaFeeDf.rename(columns=lambda x:x.replace('?"sku"','sku').replace('-','_').lower())
    fbaFeeDf.insert(0, 'date', datetime.now(timezone.utc).date())
    fbaFeeDf['date'] = pd.to_datetime(fbaFeeDf['date'])

    req_columns = [
        'date',
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
        'expected_fulfillment_fee_per_unit'
    ]

    for col in req_columns:
        if col not in fbaFeeDf.columns:
            fbaFeeDf[col] = np.nan

    fbaFeeDf = fbaFeeDf[req_columns]

    schema = {
        'date': 'datetime64[ns]',
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
        'estimated_variable_closing_fee': str,
        'estimated_order_handling_fee_per_order': str,
        'estimated_pick_pack_fee_per_unit': str,
        'estimated_weight_handling_fee_per_unit': str,
        'expected_fulfillment_fee_per_unit': float
    }

    fbaFeeDf = fbaFeeDf.astype(schema)

    return fbaFeeDf

def inboundPlacementReport(filePath:str):
    try:
        inboundPlacementDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        inboundPlacementDf = pd.read_csv(filePath, encoding='ISO-8859-1')

    inboundPlacementDf = inboundPlacementDf.rename(columns=lambda x:x.replace('(','').replace(')','').replace(' ','_').lower())
    inboundPlacementDf['transaction_date'] = pd.to_datetime(inboundPlacementDf['transaction_date'])

    req_columns = [
        'transaction_date',
        'shipping_plan_id',
        'fba_shipment_id',
        'country',
        'fnsku',
        'asin',
        'planned_fba_inbound_placement_service',
        'planned_number_of_shipments',
        'compliant_number_of_shipments',
        'inbound_defect_type',
        'actual_charge_tier',
        'planned_inbound_region',
        'actual_inbound_region',
        'actual_received_quantity',
        'product_size_tier',
        'shipping_weight',
        'unit_of_weight',
        'fba_inbound_placement_service_fee_rate_per_unit',
        'eligible_applied_incentive',
        'currency',
        'total_fba_inbound_placement_service_fee_charge',
        'total_charges'
    ]

    for col in req_columns:
        if col not in inboundPlacementDf.columns:
            inboundPlacementDf[col] = np.nan

    inboundPlacementDf = inboundPlacementDf[req_columns]

    schema = {
        'transaction_date': 'datetime64[ns]',
        'shipping_plan_id': str,
        'fba_shipment_id': str,
        'country': str,
        'fnsku': str,
        'asin': str,
        'planned_fba_inbound_placement_service': str,
        'planned_number_of_shipments': float,
        'compliant_number_of_shipments': float,
        'inbound_defect_type': str,
        'actual_charge_tier': str,
        'planned_inbound_region': str,
        'actual_inbound_region': str,
        'actual_received_quantity': float,
        'product_size_tier': str,
        'shipping_weight': float,
        'unit_of_weight': str,
        'fba_inbound_placement_service_fee_rate_per_unit': float,
        'eligible_applied_incentive': float,
        'currency': str,
        'total_fba_inbound_placement_service_fee_charge': float,
        'total_charges': float
    }

    inboundPlacementDf = inboundPlacementDf.astype(schema)

    return inboundPlacementDf

def campAttribReport(filePath:str):
    attCampDf = pd.read_excel(filePath)
    attCampDf = attCampDf.rename(columns=lambda x:x.replace('14','_14').replace(' ','_').lower())

    req_columns = [
        'date',
        'advertiser_country',
        'order_currency',
        'advertiser',
        'publisher',
        'channel',
        'campaign_name',
        'ad_group_name',
        'clicks',
        '_14_day_total_dpv',
        '_14_day_total_atc',
        '_14_day_total_purchases',
        '_14_day_total_units_sold',
        '_14_day_total_sales_',
        '_14_day_total_dpvr_clicks',
        '_14_day_total_atcr_clicks',
        '_14_day_total_purchase_rate_clicks',
        '_14_day_dpv',
        '_14_day_atc',
        '_14_day_purchases',
        '_14_day_units_sold',
        '_14_day_product_sales'
    ]

    for col in req_columns:
        if col not in attCampDf.columns:
            attCampDf[col] = np.nan

    attCampDf = attCampDf[req_columns]

    schema = {
        'date': 'datetime64[ns]',
        'advertiser_country': str,
        'order_currency': str,
        'advertiser': str,
        'publisher': str,
        'channel': str,
        'campaign_name': str,
        'ad_group_name': str,
        'clicks': float,
        '_14_day_total_dpv': float,
        '_14_day_total_atc': float,
        '_14_day_total_purchases': float,
        '_14_day_total_units_sold': float,
        '_14_day_total_sales_': float,
        '_14_day_total_dpvr_clicks': float,
        '_14_day_total_atcr_clicks': float,
        '_14_day_total_purchase_rate_clicks': float,
        '_14_day_dpv': float,
        '_14_day_atc': float,
        '_14_day_purchases': float,
        '_14_day_units_sold': float,
        '_14_day_product_sales': float
    }

    attCampDf = attCampDf.astype(schema)

    return attCampDf

def invWarehouseLoc(filePath:str):
    invWarehouseDf = pd.read_csv(filePath)
    invWarehouseDf = invWarehouseDf.rename(columns=lambda x:x.replace(' ','_').replace('/','_').lower())

    invWarehouseDf['date'] = pd.to_datetime(invWarehouseDf['date'])

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

    for col in req_columns:
        if col not in invWarehouseDf.columns:
            invWarehouseDf[col] = np.nan

    invWarehouseDf = invWarehouseDf[req_columns]

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

    invWarehouseDf = invWarehouseDf.astype(schema)
    return invWarehouseDf

def spAdvertisedReport(filePath:str, marketplace:str):
    spAdvertisedDf = pd.read_excel(filePath)
    spAdvertisedDf = spAdvertisedDf.rename(columns=lambda x:x.replace(' ','_').replace('-','_').replace('(','').replace(')','')
                                                                .replace('#','').replace('$','').replace('7','_7')
                                                                .lower()
                                                                .replace('total_advertising_cost_of_sales_acos_','advertising_cost_of_sales_acos_')
                                                                .replace('total_return_on_advertising_spend_roas','return_on_advertising_spend_roas')
                                            )
    
    spAdvertisedDf.insert(0, 'marketplace', marketplace)
    req_columns = [
        'marketplace',
        'date',
        'portfolio_name',
        'currency',
        'campaign_name',
        'ad_group_name',
        'advertised_sku',
        'advertised_asin',
        'impressions',
        'clicks',
        'click_thru_rate_ctr',
        'cost_per_click_cpc',
        'spend',
        '_7_day_total_sales_',
        'advertising_cost_of_sales_acos_',
        'return_on_advertising_spend_roas',
        '_7_day_total_orders_',
        '_7_day_total_units_',
        '_7_day_conversion_rate',
        '_7_day_advertised_sku_units_',
        '_7_day_other_sku_units_',
        '_7_day_advertised_sku_sales_',
        '_7_day_other_sku_sales_',
        'retailer'
    ]

    addColumns = [
        'retailer'
    ]

    for col in addColumns:
        if col not in spAdvertisedDf.columns:
            spAdvertisedDf[col] = np.nan

    missingColumns = set(req_columns) - set(spAdvertisedDf.columns)
    newColumns = set(spAdvertisedDf.columns) - set(req_columns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    spAdvertisedDf = spAdvertisedDf[req_columns]

    schema = {
        'marketplace': str,
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'currency': str,
        'campaign_name': str,
        'ad_group_name': str,
        'advertised_sku': str,
        'advertised_asin': str,
        'impressions': float,
        'clicks': float,
        'click_thru_rate_ctr': float,
        'cost_per_click_cpc': float,
        'spend': float,
        '_7_day_total_sales_': float,
        'advertising_cost_of_sales_acos_': float,
        'return_on_advertising_spend_roas': float,
        '_7_day_total_orders_': float,
        '_7_day_total_units_': float,
        '_7_day_conversion_rate': float,
        '_7_day_advertised_sku_units_': float,
        '_7_day_other_sku_units_': float,
        '_7_day_advertised_sku_sales_': float,
        '_7_day_other_sku_sales_': float,
        'retailer': str
    }

    spAdvertisedDf = spAdvertisedDf.astype(schema)

    return spAdvertisedDf

def sdAdvertisedReport(filePath:str, marketplace:str):
    sdAdvertisedDf = pd.read_excel(filePath)
    sdAdvertisedDf = sdAdvertisedDf.rename(columns=lambda x:x.replace(' ','_').replace('-','_').replace('(','').replace(')','')
                                                            .replace('#','').replace('$','').replace('14','_14').replace(',','')
                                                            .lower()
                                                            .replace('total_advertising_cost_of_sales_acos_','advertising_cost_of_sales_acos_')
                                                            .replace('total_return_on_advertising_spend_roas','return_on_advertising_spend_roas')
                                        )

    sdAdvertisedDf.insert(0, 'marketplace', marketplace)
    req_columns = [
        'marketplace',
        'date',
        'currency',
        'campaign_name',
        'portfolio_name',
        'cost_type',
        'ad_group_name',
        'bid_optimization',
        'advertised_sku',
        'advertised_asin',
        'impressions',
        'viewable_impressions',
        'clicks',
        'click_thru_rate_ctr',
        '_14_day_detail_page_views_dpv',
        'spend',
        'cost_per_click_cpc',
        'cost_per_1000_viewable_impressions_vcpm',
        'advertising_cost_of_sales_acos_',
        'return_on_advertising_spend_roas',
        '_14_day_total_orders_',
        '_14_day_total_units_',
        '_14_day_total_sales_',
        '_14_day_new_to_brand_orders_',
        '_14_day_new_to_brand_sales',
        '_14_day_new_to_brand_units_',
        'advertising_cost_of_sales_acos___click',
        'return_on_advertising_spend_roas___click',
        '_14_day_total_orders____click',
        '_14_day_total_units____click',
        '_14_day_total_sales___click',
        '_14_day_new_to_brand_orders____click',
        '_14_day_new_to_brand_sales___click',
        '_14_day_new_to_brand_units____click'
    ]

    missingColumns = set(req_columns) - set(sdAdvertisedDf.columns)
    newColumns = set(sdAdvertisedDf.columns) - set(req_columns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    sdAdvertisedDf = sdAdvertisedDf[req_columns]

    schema = {
        'marketplace': str,
        'date': 'datetime64[ns]',
        'currency': str,
        'campaign_name': str,
        'portfolio_name': str,
        'cost_type': str,
        'ad_group_name': str,
        'bid_optimization': str,
        'advertised_sku': str,
        'advertised_asin': str,
        'impressions': float,
        'viewable_impressions': float,
        'clicks': float,
        'click_thru_rate_ctr': float,
        '_14_day_detail_page_views_dpv': float,
        'spend': float,
        'cost_per_click_cpc': float,
        'cost_per_1000_viewable_impressions_vcpm': float,
        'advertising_cost_of_sales_acos_': float,
        'return_on_advertising_spend_roas': float,
        '_14_day_total_orders_': float,
        '_14_day_total_units_': float,
        '_14_day_total_sales_': float,
        '_14_day_new_to_brand_orders_': float,
        '_14_day_new_to_brand_sales': float,
        '_14_day_new_to_brand_units_': float,
        'advertising_cost_of_sales_acos___click': float,
        'return_on_advertising_spend_roas___click': float,
        '_14_day_total_orders____click': float,
        '_14_day_total_units____click': float,
        '_14_day_total_sales___click': float,
        '_14_day_new_to_brand_orders____click': float,
        '_14_day_new_to_brand_sales___click': float,
        '_14_day_new_to_brand_units____click': float
    }

    sdAdvertisedDf = sdAdvertisedDf.astype(schema)

    return sdAdvertisedDf

def spTargetingReport(filePath:str, marketplace:str):
    spTargetingDf = pd.read_excel(filePath)
    spTargetingDf = spTargetingDf.rename(columns=lambda x:x.replace(' ','_').replace('-','_').replace('(','').replace(')','')
                                                            .replace('#','').replace('$','').replace(',','').replace('7','_7')
                                                            .lower()
                                        )

    spTargetingDf.insert(0, 'marketplace', marketplace)
    req_columns = [
        'marketplace',
        'date',
        'portfolio_name',
        'currency',
        'campaign_name',
        'ad_group_name',
        'targeting',
        'match_type',
        'impressions',
        'top_of_search_impression_share',
        'clicks',
        'click_thru_rate_ctr',
        'cost_per_click_cpc',
        'spend',
        'total_advertising_cost_of_sales_acos_',
        'total_return_on_advertising_spend_roas',
        '_7_day_total_sales_',
        '_7_day_total_orders_',
        '_7_day_total_units_',
        '_7_day_conversion_rate',
        '_7_day_advertised_sku_units_',
        '_7_day_other_sku_units_',
        '_7_day_advertised_sku_sales_',
        '_7_day_other_sku_sales_',
        'retailer'
    ]

    addColumns = [
        'retailer'
    ]

    for col in addColumns:
        if col not in spTargetingDf.columns:
            spTargetingDf[col] = np.nan

    missingColumns = set(req_columns) - set(spTargetingDf.columns)
    newColumns = set(spTargetingDf.columns) - set(req_columns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    spTargetingDf = spTargetingDf[req_columns]

    schema = {
        'marketplace': str,
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'currency': str,
        'campaign_name': str,
        'ad_group_name': str,
        'targeting': str,
        'match_type': str,
        'impressions': float,
        'top_of_search_impression_share': float,
        'clicks': float,
        'click_thru_rate_ctr': float,
        'cost_per_click_cpc': float,
        'spend': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_7_day_total_sales_': float,
        '_7_day_total_orders_': float,
        '_7_day_total_units_': float,
        '_7_day_conversion_rate': float,
        '_7_day_advertised_sku_units_': float,
        '_7_day_other_sku_units_': float,
        '_7_day_advertised_sku_sales_': float,
        '_7_day_other_sku_sales_': float,
        'retailer': str
    }

    spTargetingDf = spTargetingDf.astype(schema)

    return spTargetingDf

def shipmentsReport(filePath:str):
    try:
        shipmentsDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        shipmentsDf = pd.read_csv(filePath, encoding='ISO-8859-1')
        
    shipmentsDf = shipmentsDf.rename(columns=lambda x:x.replace(' ','_').lower())
    shipmentsDf['created'] = pd.to_datetime(shipmentsDf['created'])
    shipmentsDf['last_updated'] = pd.to_datetime(shipmentsDf['last_updated'])

    req_columns = [
        'shipment_name',
        'shipment_id',
        'created',
        'last_updated',
        'ship_to',
        'skus',
        'units_expected',
        'units_located',
        'status'
    ]

    for col in req_columns:
        if col not in shipmentsDf.columns:
            shipmentsDf[col] = np.nan

    shipmentsDf = shipmentsDf[req_columns]

    schema = {
        'shipment_name': str,
        'shipment_id': str,
        'created': 'datetime64[ns]',
        'last_updated': 'datetime64[ns]',
        'ship_to': str,
        'skus': float,
        'units_expected': float,
        'units_located': float,
        'status': str
    }

    shipmentsDf = shipmentsDf.astype(schema)

    return shipmentsDf

def reimbursementReport(filePath:str):
    try:
        reimbursementDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        reimbursementDf = pd.read_csv(filePath, encoding='ISO-8859-1')

    reimbursementDf = reimbursementDf.rename(columns=lambda x:x.replace(' ','_').replace('-','_').lower())
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
        if col not in reimbursementDf:
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
        'original_reimbursement_id': float,
        'original_reimbursement_type': str
    }

    reimbursementDf = reimbursementDf.astype(schema)

    return reimbursementDf

def ledgerReport(filePath:str):
    try:
        ledgerDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        ledgerDf = pd.read_csv(filePath, encoding='ISO-8859-1')

    ledgerDf = ledgerDf.rename(columns=lambda x:x.replace(' ','_').lower())
    ledgerDf['date'] = pd.to_datetime(ledgerDf['date'])
    ledgerDf['date_and_time'] = pd.to_datetime(ledgerDf['date_and_time'])

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

def replacementReport(filePath:str):
    try:
        replacementDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        replacementDf = pd.read_csv(filePath, encoding='ISO-8859-1')

    replacementDf = replacementDf.rename(columns=lambda x:x.replace('?"shipment-date"','shipment_date').replace(' ','_').replace('-','_').lower())
    replacementDf['shipment_date'] = pd.to_datetime(replacementDf['shipment_date'], utc=True)

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
        'replacement_reason_code': str,
        'replacement_amazon_order_id': str,
        'original_amazon_order_id': str
    }

    replacementDf = replacementDf.astype(schema)

    return replacementDf

def customerReturnReport(filePath:str):
    try:
        customerReturnDf = pd.read_csv(filePath)
    except UnicodeDecodeError:
        customerReturnDf = pd.read_csv(filePath, encoding='ISO-8859-1')

    customerReturnDf = customerReturnDf.rename(columns=lambda x:x.replace(' ','_').replace('-','_').lower())
    customerReturnDf['return_date'] = pd.to_datetime(customerReturnDf['return_date'], utc=True)

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
        if col not in customerReturnDf.columns:
            customerReturnDf[col] = np.nan

    customerReturnDf = customerReturnDf[req_columns]

    schema = {
        'return_date': 'datetime64[ns, UTC]',
        'order_id': str,
        'sku': str,
        'asin': str,
        'fnsku': str,
        'product_name': str,
        'quantity': float,
        'fulfillment_center_id': str,
        'detailed_disposition': str,
        'reason': str,
        'status': str,
        'license_plate_number': str,
        'customer_comments': str
    }

    customerReturnDf = customerReturnDf.astype(schema)

    return customerReturnDf

def spPlacementReport(filePath, marketplace):
    dfInit = pd.read_excel(filePath)
    dfInit = dfInit.rename(columns=lambda x:x.replace(' ','_').replace('-','').replace('(','')
                                            .replace(')','').replace('#','').replace('7_Day_','')
                                            .lower()
                          )
    dfInit.insert(0,'marketplace', marketplace)

    addColumns = [
        'retailer'
    ]

    for col in addColumns:
        if col not in dfInit.columns:
            dfInit[col] = np.nan

    reqColumns = [
        'date',
        'marketplace',
        'portfolio_name',
        'campaign_name',
        'bidding_strategy',
        'placement',
        'impressions',
        'clicks',
        'total_orders_',
        'total_units_',
        'currency',
        'spend',
        'total_sales_',
        'retailer',
        'total_advertising_cost_of_sales_acos_',
        'cost_per_click_cpc',
        'total_return_on_advertising_spend_roas'
    ]

    missingColumns = set(reqColumns) - set(dfInit.columns)
    newColumns = set(dfInit.columns) - set(reqColumns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    placementDfFinal = dfInit[reqColumns]

    schema = {
        'date': 'datetime64[ns]',
        'marketplace': str,
        'portfolio_name': str,
        'campaign_name': str,
        'bidding_strategy': str,
        'placement': str,
        'impressions': float,
        'clicks': float,
        'total_orders_': float,
        'total_units_': float,
        'currency': str,
        'spend': float,
        'total_sales_': float,
        'retailer': str,
        'total_advertising_cost_of_sales_acos_': float,
        'cost_per_click_cpc': float,
        'total_return_on_advertising_spend_roas': float
    }

    placementDfFinal = placementDfFinal.astype(schema)
    
    return placementDfFinal

def spBulkReport(filePath, date, marketplace):
    sheet_names = pd.ExcelFile(filePath).sheet_names
    for name in sheet_names:
        if 'products' in name.lower():
            spSheet = name
    df = pd.read_excel(filePath,spSheet)
    df = df.rename(columns=lambda x:x.replace(' ','_').replace('-','').replace('(','').replace(')','').replace('#','').lower())

    df.insert(0,'marketplace',marketplace)
    df.insert(0,'date',date)

    reqColumns = [
        'date',
        'marketplace',
        'product',
        'entity',
        'operation',
        'campaign_id',
        'ad_group_id',
        'portfolio_id',
        'ad_id',
        'keyword_id',
        'product_targeting_id',
        'campaign_name',
        'ad_group_name',
        'campaign_name_informational_only',
        'ad_group_name_informational_only',
        'portfolio_name_informational_only',
        'start_date',
        'end_date',
        'targeting_type',
        'state',
        'campaign_state_informational_only',
        'ad_group_state_informational_only',
        'daily_budget',
        'sku',
        'asin_informational_only',
        'eligibility_status_informational_only',
        'reason_for_ineligibility_informational_only',
        'ad_group_default_bid',
        'ad_group_default_bid_informational_only',
        'bid',
        'keyword_text',
        'native_language_keyword',
        'native_language_locale',
        'match_type',
        'bidding_strategy',
        'placement',
        'percentage',
        'product_targeting_expression',
        'resolved_product_targeting_expression_informational_only',
        'impressions',
        'clicks',
        'clickthrough_rate',
        'spend',
        'sales',
        'orders',
        'units',
        'conversion_rate',
        'acos',
        'cpc',
        'roas'
    ]

    missingColumns = set(reqColumns) - set(df.columns)
    newColumns = set(df.columns) - set(reqColumns)

    if missingColumns:
        message = f'Missing columns: {", ".join(missingColumns)}'
        raise ValueError(message)
    if newColumns:
        message = f'New columns: {", ".join(newColumns)}'
        print(message)

    df = df[reqColumns]

    schema = {
        'date': 'datetime64[ns]',
        'marketplace': str,
        'product': str,
        'entity': str,
        'operation': str,
        'campaign_id': str,
        'ad_group_id': str,
        'portfolio_id': str,
        'ad_id': str,
        'keyword_id': str,
        'product_targeting_id': str,
        'campaign_name': str,
        'ad_group_name': str,
        'campaign_name_informational_only': str,
        'ad_group_name_informational_only': str,
        'portfolio_name_informational_only': str,
        'start_date': str,
        'end_date': str,
        'targeting_type': str,
        'state': str,
        'campaign_state_informational_only': str,
        'ad_group_state_informational_only': str,
        'daily_budget': float,
        'sku': str,
        'asin_informational_only': str,
        'eligibility_status_informational_only': str,
        'reason_for_ineligibility_informational_only': str,
        'ad_group_default_bid': float,
        'ad_group_default_bid_informational_only': float,
        'bid': float,
        'keyword_text': str,
        'native_language_keyword': str,
        'native_language_locale': str,
        'match_type': str,
        'bidding_strategy': str,
        'placement': str,
        'percentage': float,
        'product_targeting_expression': str,
        'resolved_product_targeting_expression_informational_only': str,
        'impressions': float,
        'clicks': float,
        'clickthrough_rate': float,
        'spend': float,
        'sales': float,
        'orders': float,
        'units': float,
        'conversion_rate': float,
        'acos': float,
        'cpc': float,
        'roas': float
    }

    df = df.astype(schema)
    return df

def sbBulkReport(filePath, date, marketplace):
    sheet_names = pd.ExcelFile(filePath).sheet_names
    for name in sheet_names:
        if 'brands' in name.lower():
            spSheet = name
    df = pd.read_excel(filePath,spSheet)
    df = df.rename(columns=lambda x:x.replace(' ','_').replace('-','').replace('(','').replace(')','').replace('#','').lower())

    df.insert(0,'marketplace',marketplace)
    df.insert(0,'date',date)

    reqColumns = [
        'date',
        'marketplace',
        'product',
        'entity',
        'operation',
        'campaign_id',
        'draft_campaign_id',
        'portfolio_id',
        'ad_group_id',
        'keyword_id',
        'product_targeting_id',
        'campaign_name',
        'campaign_name_informational_only',
        'portfolio_name_informational_only',
        'start_date',
        'end_date',
        'state',
        'campaign_state_informational_only',
        'campaign_serving_status_informational_only',
        'budget_type',
        'budget',
        'bid_optimization',
        'bid_multiplier',
        'bid',
        'keyword_text',
        'match_type',
        'product_targeting_expression',
        'resolved_product_targeting_expression_informational_only',
        'ad_format',
        'ad_format_informational_only',
        'landing_page_url',
        'landing_page_asins',
        'landing_page_type_informational_only',
        'brand_entity_id',
        'brand_name',
        'brand_logo_asset_id',
        'brand_logo_url_informational_only',
        'custom_image_asset_id',
        'creative_headline',
        'creative_asins',
        'video_media_ids',
        'creative_type',
        'impressions',
        'clicks',
        'clickthrough_rate',
        'spend',
        'sales',
        'orders',
        'units',
        'conversion_rate',
        'acos',
        'cpc',
        'roas'
    ]

    missingColumns = set(reqColumns) - set(df.columns)
    newColumns = set(df.columns) - set(reqColumns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    df = df[reqColumns]

    schema = {
        'date': 'datetime64[ns]',
        'marketplace': str,
        'product': str,
        'entity': str,
        'operation': str,
        'campaign_id': str,
        'draft_campaign_id': str,
        'portfolio_id': str,
        'ad_group_id': str,
        'keyword_id': str,
        'product_targeting_id': str,
        'campaign_name': str,
        'campaign_name_informational_only': str,
        'portfolio_name_informational_only': str,
        'start_date': str,
        'end_date': str,
        'state': str,
        'campaign_state_informational_only': str,
        'campaign_serving_status_informational_only': str,
        'budget_type': str,
        'budget': float,
        'bid_optimization': str,
        'bid_multiplier': str,
        'bid': float,
        'keyword_text': str,
        'match_type': str,
        'product_targeting_expression': str,
        'resolved_product_targeting_expression_informational_only': str,
        'ad_format': str,
        'ad_format_informational_only': str,
        'landing_page_url': str,
        'landing_page_asins': str,
        'landing_page_type_informational_only': str,
        'brand_entity_id': str,
        'brand_name': str,
        'brand_logo_asset_id': str,
        'brand_logo_url_informational_only': str,
        'custom_image_asset_id': str,
        'creative_headline': str,
        'creative_asins': str,
        'video_media_ids': str,
        'creative_type': str,
        'impressions': float,
        'clicks': float,
        'clickthrough_rate': float,
        'spend': float,
        'sales': float,
        'orders': float,
        'units': float,
        'conversion_rate': float,
        'acos': float,
        'cpc': float,
        'roas': float
    }

    df = df.astype(schema)
    return df

def sdBulkReport(filePath, date, marketplace):
    sheet_names = pd.ExcelFile(filePath).sheet_names
    for name in sheet_names:
        if 'display' in name.lower():
            spSheet = name
    df = pd.read_excel(filePath,spSheet)
    df = df.rename(columns=lambda x:x.replace(' ','_').replace('-','').replace('(','').replace(')','').replace('#','').replace('&','').lower())

    df.insert(0,'marketplace',marketplace)
    df.insert(0,'date',date)

    reqColumns = [
        'date',
        'marketplace',
        'product',
        'entity',
        'operation',
        'campaign_id',
        'portfolio_id',
        'ad_group_id',
        'ad_id',
        'targeting_id',
        'campaign_name',
        'ad_group_name',
        'campaign_name_informational_only',
        'ad_group_name_informational_only',
        'portfolio_name_informational_only',
        'start_date',
        'end_date',
        'state',
        'campaign_state_informational_only',
        'ad_group_state_informational_only',
        'tactic',
        'budget_type',
        'budget',
        'sku',
        'asin_informational_only',
        'ad_group_default_bid',
        'ad_group_default_bid_informational_only',
        'bid',
        'bid_optimization',
        'cost_type',
        'targeting_expression',
        'resolved_targeting_expression_informational_only',
        'impressions',
        'clicks',
        'clickthrough_rate',
        'spend',
        'sales',
        'orders',
        'units',
        'conversion_rate',
        'acos',
        'cpc',
        'roas',
        'viewable_impressions',
        'sales_views__clicks',
        'orders_views__clicks',
        'units_views__clicks',
        'acos_views__clicks',
        'roas_views__clicks'
    ]

    missingColumns = set(reqColumns) - set(df.columns)
    newColumns = set(df.columns) - set(reqColumns)

    if missingColumns:
        raise ValueError(f"Missing columns: {', '.join(missingColumns)}")

    if newColumns:
        print(f"New columns: {', '.join(newColumns)}")

    df = df[reqColumns]

    schema = {
        'date': 'datetime64[ns]',
        'marketplace': str,
        'product': str,
        'entity': str,
        'operation': str,
        'campaign_id': str,
        'portfolio_id': str,
        'ad_group_id': str,
        'ad_id': str,
        'targeting_id': str,
        'campaign_name': str,
        'ad_group_name': str,
        'campaign_name_informational_only': str,
        'ad_group_name_informational_only': str,
        'portfolio_name_informational_only': str,
        'start_date': str,
        'end_date': str,
        'state': str,
        'campaign_state_informational_only': str,
        'ad_group_state_informational_only': str,
        'tactic': str,
        'budget_type': str,
        'budget': float,
        'sku': str,
        'asin_informational_only': str,
        'ad_group_default_bid': float,
        'ad_group_default_bid_informational_only': float,
        'bid': float,
        'bid_optimization': str,
        'cost_type': str,
        'targeting_expression': str,
        'resolved_targeting_expression_informational_only': str,
        'impressions': float,
        'clicks': float,
        'clickthrough_rate': float,
        'spend': float,
        'sales': float,
        'orders': float,
        'units': float,
        'conversion_rate': float,
        'acos': float,
        'cpc': float,
        'roas': float,
        'viewable_impressions': float,
        'sales_views__clicks': float,
        'orders_views__clicks': float,
        'units_views__clicks': float,
        'acos_views__clicks': float,
        'roas_views__clicks': float
    }

    df = df.astype(schema)
    return df

def spPlacementMulitMarketReport(file_path):
    df = pd.read_excel(file_path)
    df = df.rename(columns=lambda x:x.replace('(','')
                                    .replace(')','')
                                    .replace('#','')
                                    .replace('-','')
                                    .replace(' ','_')
                                    .replace('7','_7')
                                    .replace('__','_')
                                    .lower()
                  )
    req_columns = [
        'date',
        'portfolio_name',
        'currency_converted',
        'currency_not_converted',
        'campaign_name',
        'retailer',
        'country',
        'bidding_strategy',
        'placement',
        'impressions',
        'clicks',
        'cost_per_click_cpc_converted',
        'cost_per_click_cpc_not_converted',
        'spend_converted',
        'spend_not_converted',
        '_7_day_total_sales_converted',
        '_7_day_total_sales_not_converted',
        'total_advertising_cost_of_sales_acos_',
        'total_return_on_advertising_spend_roas',
        '_7_day_total_orders_',
        '_7_day_total_units_'
    ]

    missing_columns = set(req_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    new_columns = set(df.columns) - set(req_columns)
    if new_columns:
        print(f"New columns detected: {', '.join(new_columns)}")

    df = df[req_columns]

    schema = {
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'currency_converted': str,
        'currency_not_converted': str,
        'campaign_name': str,
        'retailer': str,
        'country': str,
        'bidding_strategy': str,
        'placement': str,
        'impressions': float,
        'clicks': float,
        'cost_per_click_cpc_converted': float,
        'cost_per_click_cpc_not_converted': float,
        'spend_converted': float,
        'spend_not_converted': float,
        '_7_day_total_sales_converted': float,
        '_7_day_total_sales_not_converted': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_7_day_total_orders_': float,
        '_7_day_total_units_': float,
    }
    df = df.astype(schema)

    return df

def spAdvertisedMultiMarketReport(file_path):
    df = pd.read_excel(file_path)
    df = df.rename(columns=lambda x: x.replace('7','_7')
                                      .replace('(','')
                                      .replace(')','')
                                      .replace('-','')
                                      .replace('#','')
                                      .replace(' ','_')
                                      .replace('__','_')
                                      .lower()
                   )
    
    req_columns = [
        'date',
        'portfolio_name',
        'currency_converted',
        'currency_not_converted',
        'campaign_name',
        'ad_group_name',
        'retailer',
        'country',
        'advertised_sku',
        'advertised_asin',
        'impressions',
        'clicks',
        'clickthru_rate_ctr',
        'cost_per_click_cpc_converted',
        'cost_per_click_cpc_not_converted',
        'spend_converted',
        'spend_not_converted',
        '_7_day_total_sales_converted',
        '_7_day_total_sales_not_converted',
        'total_advertising_cost_of_sales_acos_',
        'total_return_on_advertising_spend_roas',
        '_7_day_total_orders_',
        '_7_day_total_units_',
        '_7_day_conversion_rate',
        '_7_day_advertised_sku_units_',
        '_7_day_other_sku_units_',
        '_7_day_advertised_sku_sales_converted',
        '_7_day_advertised_sku_sales_not_converted',
        '_7_day_other_sku_sales_converted_',
        '_7_day_other_sku_sales_not_converted'
    ]

    missing_columns = set(req_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    new_columns = set(df.columns) - set(req_columns)
    if new_columns:
        print(f"New columns found: {', '.join(new_columns)}")

    df = df[req_columns]

    schema = {
        'date': 'datetime64[ns]',
        'portfolio_name': str,
        'currency_converted': str,
        'currency_not_converted': str,
        'campaign_name': str,
        'ad_group_name': str,
        'retailer': str,
        'country': str,
        'advertised_sku': str,
        'advertised_asin': str,
        'impressions': float,
        'clicks': float,
        'clickthru_rate_ctr': float,
        'cost_per_click_cpc_converted': float,
        'cost_per_click_cpc_not_converted': float,
        'spend_converted': float,
        'spend_not_converted': float,
        '_7_day_total_sales_converted': float,
        '_7_day_total_sales_not_converted': float,
        'total_advertising_cost_of_sales_acos_': float,
        'total_return_on_advertising_spend_roas': float,
        '_7_day_total_orders_': float,
        '_7_day_total_units_': float,
        '_7_day_conversion_rate': float,
        '_7_day_advertised_sku_units_': float,
        '_7_day_other_sku_units_': float,
        '_7_day_advertised_sku_sales_converted': float,
        '_7_day_advertised_sku_sales_not_converted': float,
        '_7_day_other_sku_sales_converted_': float,
        '_7_day_other_sku_sales_not_converted': float
    }
    df = df.astype(schema)

    return df

