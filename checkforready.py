import requests
import json

def ready_check(pageId):
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'channel-type': 'web',
        'content-type': 'application/json',
        'origin': 'https://webapp.flash.co',
        'priority': 'u=1, i',
        'referer': 'https://webapp.flash.co/',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
        'x-api-key': 'BROWSER_API_KEY_EgHe7D4ZdyhRbEUos4q0MUA0CTi2w4TqiACgmRULq6nIUhBAH2dxu47KYVub4yhmt9K4UjBvu1dxYMGEjF4GdE54o6TXew5Tsbq41f06KDMhm4eP',
        'x-country-code': 'IN',
        'x-guest-id': '779b02ac-aee9-4bd6-b5b9-cdc1ded23831',
        'x-timezone': 'Asia/Calcutta',
    }

    params = {
        'product_detail_hash': pageId,
    }

    try:
        response = requests.get('https://apiv3.flash.tech/agents/product-detail-steps', params=params, headers=headers, timeout=180)
        response.raise_for_status()
        
        response_data = response.json()
        try:
            if response_data['message']:
                return response_data['message']
        except:
            pass
        if response_data['data']['progressBar']['progressPercentage']['value']:
            percentage = response_data['data']['progressBar']['progressPercentage']['value']
            return percentage
    except requests.RequestException as e:
        print(f"Request error for pageId {pageId}: {e}")
        return 0
    
if __name__ == "__main__":
    print(ready_check("jacuCWPJ"))