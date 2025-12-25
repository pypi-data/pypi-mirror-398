import requests
from datetime import datetime, timezone, timedelta
import json
from .ratelimit import RateLimiter
from .api import get_sellerId

def raw_sku_attributes(marketplace_action, access_token, sku):
    """
    This will pull SKU attributes in specific Marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - sku: SKU to pull the attribute details

    return:
    - json format of the SKU attributes
    """
    # get sellerID
    try:
        sellerId = get_sellerId(marketplace_action, access_token, sku)
    except KeyError as e:
        raise ValueError(f'❌ Error in getting sellerID: {e}')

    # API Pull
    rate_limiter = RateLimiter(tokens_per_second=5, capacity=10)
    regionUrl, marketplace_id = marketplace_action()

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
        return json.dumps(response.json(), indent=4)
    except Exception as e:
        raise ValueError(f'{response.status_code} - {response.text}')

def get_productType(marketplace_action, access_token, sellerId, sku):
    """
    This will pull SKU productType in specific Marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - sellerId: sellerId of the account
    - sku: SKU to pull the attribute details

    return:
    - productType of the SKU
    """
    # get productType
    print('Getting product type...')
    try:
        region_url, marketplace = marketplace_action()
        endpoint = f"/listings/2021-08-01/items/{sellerId}/{sku}?marketplaceIds={marketplace}&includedData=summaries"
        url = region_url + endpoint

        headers = {
            "accept": "application/json",
            "x-amz-access-token": access_token
            }
        response = requests.get(url, headers=headers)
        productType = response.json()['summaries'][0]['productType']
        print(f'SKU product type is: {productType}')
        return productType
    except KeyError as e:
        raise ValueError(f'❌ Error getting product type: {e}')

def patch_builder(updates):
    """
    This will create the correct patch in updating product attributes base on available data.

    Parameter:
    - updates: json format of sku and update values
        e.g.: {'sku': 'SMAPLE-SKU', 'salePrice': 55.99, 'main_image_url': 'https://m.public.com/images/A/yourimage.jpg'}

    return:
    - json format patch data
    """
    # set sale dates
    start_date = datetime.now(timezone.utc).isoformat()
    end_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

    patches = []

    # purhcasable offer patch
    purchasable_offers = {}

    if 'salePrice' in updates:
        salePrice = updates['salePrice']
        purchasable_offers["discounted_price"] = [
                    {
                        "schedule": [
                            {
                              "end_at": f"{end_date}",
                              "start_at": f"{start_date}",
                              "value_with_tax": salePrice
                            }
                        ]
                    }
                ]

    if 'ourPrice' in updates:
        ourPrice = updates['ourPrice']
        purchasable_offers["our_price"] = [
                    {
                        "schedule": [
                            {
                                "value_with_tax": ourPrice
                            }
                        ]
                    }
                ]

    if purchasable_offers:
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/purchasable_offer",
                    "value": [purchasable_offers]
                }
        )

    # list price patch
    if 'listPrice' in updates:
        listPrice = updates['listPrice']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/list_price",
                    "value": [
                        {
                            "value": listPrice
                        }
                    ]
                }
        )

    # images patche
    if 'main_image_url' in updates:
        main_image_url = updates['main_image_url']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/main_product_image_locator",
                    "value": [
                        {
                            "media_location": f"{main_image_url}"
                        }
                    ]
                }
        )

    if 'other_product_image_locator_1' in updates:
        other_product_image_locator_1 = updates['other_product_image_locator_1']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_1",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_1}"
                        }
                    ]
                }
        )
    
    if 'other_product_image_locator_2' in updates:
        other_product_image_locator_2 = updates['other_product_image_locator_2']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_2",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_2}"
                        }
                    ]
                }
        )

    if 'other_product_image_locator_3' in updates:
        other_product_image_locator_3 = updates['other_product_image_locator_3']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_3",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_3}"
                        }
                    ]
                }
        )
    
    if 'other_product_image_locator_4' in updates:
        other_product_image_locator_4 = updates['other_product_image_locator_4']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_4",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_4}"
                        }
                    ]
                }
        )

    if 'other_product_image_locator_5' in updates:
        other_product_image_locator_5 = updates['other_product_image_locator_5']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_5",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_5}"
                        }
                    ]
                }
        )

    if 'other_product_image_locator_6' in updates:
        other_product_image_locator_6 = updates['other_product_image_locator_6']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_6",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_6}"
                        }
                    ]
                }
        )

    if 'other_product_image_locator_7' in updates:
        other_product_image_locator_7 = updates['other_product_image_locator_7']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_7",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_7}"
                        }
                    ]
                }
        )
    
    if 'other_product_image_locator_8' in updates:
        other_product_image_locator_8 = updates['other_product_image_locator_8']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/other_product_image_locator_8",
                    "value": [
                        {
                            "media_location": f"{other_product_image_locator_8}"
                        }
                    ]
                }
        )

    # product name patch
    if 'item_name' in updates:
        item_name = updates['item_name']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/item_name",
                    "value": [
                        {
                            "value": f"{item_name}"
                        }
                    ]
                }
        )

    # product description patch
    if 'product_description' in updates:
        product_description = updates['product_description']
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/product_description",
                    "value": [
                        {
                            "value": f"{product_description}"
                        }
                    ]
                }
        )

    # bullet points patch
    bullet_points = []
    for i in range(1, 6):
        if f'bullet_point_{i}' in updates:
            bullet_point = updates[f'bullet_point_{i}']
            bullet_points.append(
                {
                    "value": f"{bullet_point}"
                }
            )

    if bullet_points:
        patches.append(
                {
                    "op": "replace",
                    "path": "/attributes/bullet_points",
                    "value": bullet_points
                }
        )

    # return final patch
    return patches

def update_sku_attributes(marketplace_action, access_token, updates):
    """
    This will update SKU attirbutes in specific Marketplace.

    Parameter:
    - marketplace_action: the specific marketplace command to pull the data
    - access_token: matching access token of the marketplace
    - updates: json format of sku and update values
        e.g.: {'sku': 'SMAPLE-SKU', 'salePrice': 55.99, 'main_image_url': 'https://m.public.com/images/A/yourimage.jpg'}

    return:
    - product update status
    """
    # get update values
    sku = updates['sku']
    salePrice = updates.get('salePrice')
    listPrice = updates.get('listPrice')
    ourPrice = updates.get('ourPrice')
    main_image_url = updates.get('main_image_url')
    other_product_image_locator_1 = updates.get('other_product_image_locator_1')
    other_product_image_locator_2 = updates.get('other_product_image_locator_2')
    other_product_image_locator_3 = updates.get('other_product_image_locator_3')
    other_product_image_locator_4 = updates.get('other_product_image_locator_4')
    other_product_image_locator_5 = updates.get('other_product_image_locator_5')
    other_product_image_locator_6 = updates.get('other_product_image_locator_6')
    other_product_image_locator_7 = updates.get('other_product_image_locator_7')
    other_product_image_locator_8 = updates.get('other_product_image_locator_8')
    item_name = updates.get('item_name')
    product_description = updates.get('product_description')
    bullet_point_1 = updates.get('bullet_point_1')
    bullet_point_2 = updates.get('bullet_point_2')
    bullet_point_3 = updates.get('bullet_point_3')
    bullet_point_4 = updates.get('bullet_point_4')
    bullet_point_5 = updates.get('bullet_point_5')

    # get sellerId
    print('Getting seller ID...')
    try:
        sellerId = get_sellerId(marketplace_action, access_token, sku)
    except KeyError as e:
        raise ValueError(f'❌ Error getting seller ID: {e}')

    # get productType
    productType = get_productType(marketplace_action, access_token, sellerId, sku)

    # set sale dates
    start_date = datetime.now(timezone.utc).isoformat()
    end_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

    # update sale price
    region_url, marketplaceId = marketplace_action()
    endpoint = f"/listings/2021-08-01/items/{sellerId}/{sku}?marketplaceIds={marketplaceId}&includedData=issues"
    url = region_url + endpoint

    # get patches
    patches = patch_builder(updates)

    payload = {
        "patches": patches,
        "productType": f"{productType}"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-amz-access-token": access_token
    }

    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code == 200:
        msg_parts = [f"✅ Success:\n  - sku: {sku}"]

        if salePrice:
            msg_parts.append(f"  - Sale Price set to: ${salePrice}")

        if listPrice:
            msg_parts.append(f"  - List Price set to: ${listPrice}")
        
        if ourPrice:
            msg_parts.append(f"  - Our Price set to: ${ourPrice}")

        if main_image_url:
            msg_parts.append(f"  - Main Image set to: {main_image_url}")
        
        if other_product_image_locator_1:
            msg_parts.append(f"  - Other Image 1 set to: {other_product_image_locator_1}")
        
        if other_product_image_locator_2:
            msg_parts.append(f"  - Other Image 2 set to: {other_product_image_locator_2}")
        
        if other_product_image_locator_3:
            msg_parts.append(f"  - Other Image 3 set to: {other_product_image_locator_3}")
        
        if other_product_image_locator_4:
            msg_parts.append(f"  - Other Image 4 set to: {other_product_image_locator_4}")
        
        if other_product_image_locator_5:
            msg_parts.append(f"  - Other Image 5 set to: {other_product_image_locator_5}")
        
        if other_product_image_locator_6:
            msg_parts.append(f"  - Other Image 6 set to: {other_product_image_locator_6}")
        
        if other_product_image_locator_7:
            msg_parts.append(f"  - Other Image 7 set to: {other_product_image_locator_7}")

        if other_product_image_locator_8:
            msg_parts.append(f"  - Other Image 8 set to: {other_product_image_locator_8}")

        if item_name:
            msg_parts.append(f"  - Item Name set to: {item_name}")
        
        if product_description:
            msg_parts.append(f"  - Product Description updated.")

        if bullet_point_1:
            msg_parts.append(f"  - Bullet Point 1 set to: {bullet_point_1}")
        
        if bullet_point_2:
            msg_parts.append(f"  - Bullet Point 2 set to: {bullet_point_2}")
        
        if bullet_point_3:
            msg_parts.append(f"  - Bullet Point 3 set to: {bullet_point_3}")

        if bullet_point_4:
            msg_parts.append(f"  - Bullet Point 4 set to: {bullet_point_4}")
        
        if bullet_point_5:
            msg_parts.append(f"  - Bullet Point 5 set to: {bullet_point_5}")

        msg_parts.append(f"  - Submission ID: {response.json()['submissionId']}")

        success_message = "\n".join(msg_parts)
        print(success_message)
        return success_message
    else:
        raise ValueError(f"❌ Error: {json.dumps(response.json(), indent=4)}")
    
