import requests
import re
import json
import json5

def get_details_product(pageId):
    cookies = {
        'flash_guest_device': 'a39e130a-2cd2-44a1-ae3e-82f676741700',
        'flash_guest_session_id': 'd13b7f89-a1d3-45f5-b430-f7b1c9da1dcc',
        'flash_guest_device_client': 'a39e130a-2cd2-44a1-ae3e-82f676741700',
        'flash_guest_session_id_client': 'd13b7f89-a1d3-45f5-b430-f7b1c9da1dcc',
        'flash_app_host': 'false',
        'flash_country_code': 'IN',
        '_ga': 'GA1.1.958476007.1755778410',
        'WZRK_G': '_w_a39e130a-2cd2-44a1-ae3e-82f676741700',
        '_hjSession_3729003': 'eyJpZCI6ImJhMDAwMTFlLTE5NzEtNGJmOC1hYzU4LWI1MGFhNjI2Mjg4NiIsImMiOjE3NTU3Nzg0MTQ4OTUsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=',
        '_ga_C4C4J0T6HR': 'GS2.1.s1755778410$o1$g1$t1755778726$j59$l0$h0',
        '_ga_764MEH71X3': 'GS2.1.s1755778410$o1$g1$t1755778726$j59$l0$h0',
        '_hjSessionUser_3729003': 'eyJpZCI6ImY0NDMwMDI0LTM2YTctNTRlMy04YWQ0LTMzNTJkMGFmZDI2OCIsImNyZWF0ZWQiOjE3NTU3Nzg0MTQ4OTUsImV4aXN0aW5nIjp0cnVlfQ==',
        'WZRK_S_R76-65K-7K7Z': '%7B%22p%22%3A2%2C%22s%22%3A1755778411%2C%22t%22%3A1755779199%7D',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    }

    params = {
        'pageId': pageId,
    }

    response = requests.get('https://webapp.flash.co/product-details', params=params, cookies=cookies, headers=headers)
    data = response.text
    
    script_pattern = r'self\.__next_f\.push\(\[1,"5:(.*?)"\]\)'
    script_matches = re.findall(script_pattern, data, re.DOTALL)
    
    if script_matches:
        script_content = script_matches[0]
        cleaned = script_content.replace('\\"', '"')
        cleaned = cleaned.replace('\\n', '\n')
        cleaned = cleaned.replace('\\t', '\t')
        cleaned = cleaned.replace('\\r', '\r')
        cleaned = cleaned.replace('\\\\', '\\')
        
        json_start = cleaned.find('{"productId":')
        if json_start != -1:
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(cleaned[json_start:], json_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            json_str = cleaned[json_start:json_end]
            
            for attempt in range(3):
                try:
                    if attempt == 0:
                        parsed_json = json.loads(json_str)
                    elif attempt == 1:
                        fixed_json = re.sub(r',(\s*[}\]])', r'\1', json_str)
                        fixed_json = re.sub(r'\\([^"\\/bfnrt])', r'\1', fixed_json)
                        parsed_json = json.loads(fixed_json)
                    else:
                        parsed_json = json5.loads(json_str)
                    
                    return json.dumps(parsed_json, indent=2, ensure_ascii=False)
                except Exception as e:
                    if attempt == 2:
                        try:
                            product_id_match = re.search(r'"productId":"([^"]+)"', json_str)
                            product_id = product_id_match.group(1) if product_id_match else "unknown"
                            return json.dumps({
                                "productId": product_id,
                                "status": "partial_parse",
                                "message": "Full JSON parsing failed, but basic info extracted",
                                "raw_length": len(json_str)
                            }, indent=2)
                        except:
                            return json.dumps({
                                "error": "Failed to parse JSON",
                                "raw_length": len(json_str)
                            }, indent=2)
        else:
            return json.dumps({"error": "No JSON object found in response"}, indent=2)
    else:
        return json.dumps({"error": "No script content found in response"}, indent=2)

def clean_unicode_text(text: str) -> str:
    if not text or text == 'N/A':
        return text
    try:
        decoded = text.encode("utf-8").decode("unicode_escape")
        try:
            decoded = decoded.encode("latin1").decode("utf-8")
        except UnicodeDecodeError:
            pass
        return decoded
    except Exception:
        return text

if __name__ == "__main__":    
    single_result = get_details_product("pnjQjCYb")
    print(single_result)
