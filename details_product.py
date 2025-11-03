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
    patterns_to_try = [
        r'self\.__next_f\.push\(\[1,"5:(.*?)"\]\)',
        r'self\.__next_f\.push\(\[1,"7:(.*?)"\]\)',
        r'self\.__next_f\.push\(\[1,"[0-9]+:(.*?)"\]\)',
    ]
    
    script_matches = []
    used_pattern = None
    
    for pattern in patterns_to_try:
        matches = re.findall(pattern, data, re.DOTALL)
        if matches:
            script_matches = matches
            used_pattern = pattern
            break
    if script_matches:
        script_content = script_matches[0]
        cleaned = script_content.replace('\\"', '"')
        cleaned = cleaned.replace('\\n', '\n')
        cleaned = cleaned.replace('\\t', '\t')
        cleaned = cleaned.replace('\\r', '\r')
        cleaned = cleaned.replace('\\\\', '\\')
        json_starts = [
            '{"productId":',
            '{"initialData":',
            '{"widgets":',
            '{"stores":',
            '{"metadata":'
        ]
        json_start = -1
        for start_pattern in json_starts:
            json_start = cleaned.find(start_pattern)
            if json_start != -1:
                break
        if json_start != -1:
            brace_count = 0
            json_end = json_start
            in_string = False
            escape_next = False
            
            for i, char in enumerate(cleaned[json_start:], json_start):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
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
                            extracted_data = {
                                "initialData": {
                                    "widgets": []
                                },
                                "productId": None,
                                "loaderData": None,
                                "threadId": None
                            }
                            
                            product_id_match = re.search(r'"productId":"([^"]+)"', json_str)
                            if product_id_match:
                                extracted_data["productId"] = product_id_match.group(1)
                            
                            thread_id_match = re.search(r'"threadId":"([^"]+)"', json_str)
                            if thread_id_match:
                                extracted_data["threadId"] = thread_id_match.group(1)
                            
                            loader_data_match = re.search(r'"loaderData":\s*(\{.*?\})', json_str)
                            if loader_data_match:
                                try:
                                    loader_data = json.loads(loader_data_match.group(1))
                                    extracted_data["loaderData"] = loader_data
                                except:
                                    extracted_data["loaderData"] = None
                            
                            widgets_data = []
                            
                            images_match = re.search(r'"images":\s*(\[.*?\])', json_str)
                            if images_match:
                                try:
                                    images = json.loads(images_match.group(1))
                                    widgets_data.append({
                                        "images": images,
                                        "type": "IMAGE_CAROUSEL"
                                    })
                                except:
                                    image_urls = re.findall(r'"(https://[^"]*\.(?:jpg|jpeg|png|webp|gif)[^"]*)"', json_str)
                                    if image_urls:
                                        widgets_data.append({
                                            "images": image_urls[:10],
                                            "type": "IMAGE_CAROUSEL"
                                        })
                            
                            name_match = re.search(r'"name":"([^"]+)"', json_str)
                            price_match = re.search(r'"price":"([^"]+)"', json_str)
                            
                            if name_match or price_match:
                                product_header = {
                                    "type": "PRODUCT_HEADER",
                                    "name": name_match.group(1) if name_match else None,
                                    "price": price_match.group(1) if price_match else None,
                                    "stores": []
                                }
                                
                                # Extract stores for PRODUCT_HEADER - simplified approach
                                stores_data = []
                                seen_stores = set()
                                
                                # Look for all direct links first
                                direct_links = re.findall(r'"directLink":"([^"]+)"', json_str)
                                
                                # For each direct link, find its associated store data
                                for i, link in enumerate(direct_links[:10]):  # Limit to first 10
                                    # Find the position of this link
                                    link_pos = json_str.find(f'"directLink":"{link}"')
                                    if link_pos != -1:
                                        # Get context around the link
                                        start_pos = max(0, link_pos - 500)
                                        end_pos = min(len(json_str), link_pos + 500)
                                        context = json_str[start_pos:end_pos]
                                        
                                        # Extract store information from context
                                        store_info = {"directLink": link}
                                        
                                        # Determine marketplace based on the actual link domain
                                        if "amazon.in" in link or "amazon.com" in link:
                                            store_info["marketplace"] = "amazon"
                                        elif "apple.com" in link:
                                            store_info["marketplace"] = "apple"
                                        elif "croma.com" in link:
                                            store_info["marketplace"] = "croma"
                                        elif "flipkart.com" in link:
                                            store_info["marketplace"] = "flipkart"
                                        elif "iplanet.one" in link:
                                            store_info["marketplace"] = "iplanet"
                                        elif "macstation.co.in" in link:
                                            store_info["marketplace"] = "macstation"
                                        elif "newunbox.com" in link:
                                            store_info["marketplace"] = "newunbox"
                                        elif "poorvika.com" in link:
                                            store_info["marketplace"] = "poorvika"
                                        elif "quicktech.in" in link:
                                            store_info["marketplace"] = "quicktech"
                                        elif "unicornstore.in" in link:
                                            store_info["marketplace"] = "unicornstore"
                                        elif "vijaysales.com" in link:
                                            store_info["marketplace"] = "vijaysales"
                                        elif "sathya.store" in link:
                                            store_info["marketplace"] = "sathya"
                                        else:
                                            # Fallback to context-based matching
                                            marketplace_matches = list(re.finditer(r'"marketplace":"([^"]+)"', context))
                                            if marketplace_matches:
                                                link_pos_in_context = context.find(f'"directLink":"{link}"')
                                                closest_match = None
                                                min_distance = float('inf')
                                                
                                                for match in marketplace_matches:
                                                    distance = abs(match.start() - link_pos_in_context)
                                                    if distance < min_distance:
                                                        min_distance = distance
                                                        closest_match = match
                                                
                                                if closest_match:
                                                    store_info["marketplace"] = closest_match.group(1)
                                        
                                        # Set store name based on marketplace
                                        if store_info.get("marketplace") == "amazon":
                                            store_info["name"] = "Amazon.in"
                                        elif store_info.get("marketplace") == "apple":
                                            store_info["name"] = "Apple"
                                        elif store_info.get("marketplace") == "croma":
                                            store_info["name"] = "Croma"
                                        elif store_info.get("marketplace") == "flipkart":
                                            store_info["name"] = "Flipkart"
                                        elif store_info.get("marketplace") == "iplanet":
                                            store_info["name"] = "iPlanet"
                                        elif store_info.get("marketplace") == "macstation":
                                            store_info["name"] = "MacStation"
                                        elif store_info.get("marketplace") == "newunbox":
                                            store_info["name"] = "NewUnbox"
                                        elif store_info.get("marketplace") == "poorvika":
                                            store_info["name"] = "Poorvika"
                                        elif store_info.get("marketplace") == "quicktech":
                                            store_info["name"] = "QuickTech"
                                        elif store_info.get("marketplace") == "unicornstore":
                                            store_info["name"] = "Unicorn Store"
                                        elif store_info.get("marketplace") == "vijaysales":
                                            store_info["name"] = "Vijay Sales"
                                        elif store_info.get("marketplace") == "sathya":
                                            store_info["name"] = "Sathya"
                                        else:
                                            # Fallback to context-based name
                                            name_match = re.search(r'"name":"([^"]+)"', context)
                                            if name_match:
                                                store_info["name"] = name_match.group(1)
                                        
                                        # Find prices
                                        base_price_match = re.search(r'"basePrice":"([^"]+)"', context)
                                        if base_price_match:
                                            store_info["basePrice"] = base_price_match.group(1)
                                        
                                        total_price_match = re.search(r'"totalPrice":"([^"]+)"', context)
                                        if total_price_match:
                                            store_info["totalPrice"] = total_price_match.group(1)
                                        
                                        # Find affiliate link
                                        affiliate_match = re.search(r'"affiliateLink":"([^"]+)"', context)
                                        if affiliate_match:
                                            store_info["affiliateLink"] = affiliate_match.group(1)
                                        
                                        # Only add if we have marketplace
                                        if store_info.get("marketplace"):
                                            store_key = f"{store_info['marketplace']}_{link}"
                                            if store_key not in seen_stores:
                                                seen_stores.add(store_key)
                                                stores_data.append(store_info)
                                
                                # If we still need more stores, look for affiliate links
                                if len(stores_data) < 5:
                                    affiliate_links = re.findall(r'"affiliateLink":"([^"]+)"', json_str)
                                    
                                    for i, link in enumerate(affiliate_links[:5]):  # Limit to first 5
                                        link_pos = json_str.find(f'"affiliateLink":"{link}"')
                                        if link_pos != -1:
                                            start_pos = max(0, link_pos - 500)
                                            end_pos = min(len(json_str), link_pos + 500)
                                            context = json_str[start_pos:end_pos]
                                            
                                            store_info = {"affiliateLink": link}
                                            
                                            # Determine marketplace based on the actual affiliate link domain
                                            if "amazon.in" in link or "amazon.com" in link:
                                                store_info["marketplace"] = "amazon"
                                            elif "apple.com" in link:
                                                store_info["marketplace"] = "apple"
                                            elif "croma.com" in link:
                                                store_info["marketplace"] = "croma"
                                            elif "flipkart.com" in link:
                                                store_info["marketplace"] = "flipkart"
                                            elif "iplanet.one" in link:
                                                store_info["marketplace"] = "iplanet"
                                            elif "macstation.co.in" in link:
                                                store_info["marketplace"] = "macstation"
                                            elif "newunbox.com" in link:
                                                store_info["marketplace"] = "newunbox"
                                            elif "poorvika.com" in link:
                                                store_info["marketplace"] = "poorvika"
                                            elif "quicktech.in" in link:
                                                store_info["marketplace"] = "quicktech"
                                            elif "unicornstore.in" in link:
                                                store_info["marketplace"] = "unicornstore"
                                            elif "vijaysales.com" in link:
                                                store_info["marketplace"] = "vijaysales"
                                            elif "sathya.store" in link:
                                                store_info["marketplace"] = "sathya"
                                            else:
                                                # Fallback to context-based matching
                                                marketplace_matches = list(re.finditer(r'"marketplace":"([^"]+)"', context))
                                                if marketplace_matches:
                                                    link_pos_in_context = context.find(f'"affiliateLink":"{link}"')
                                                    closest_match = None
                                                    min_distance = float('inf')
                                                    
                                                    for match in marketplace_matches:
                                                        distance = abs(match.start() - link_pos_in_context)
                                                        if distance < min_distance:
                                                            min_distance = distance
                                                            closest_match = match
                                                    
                                                    if closest_match:
                                                        store_info["marketplace"] = closest_match.group(1)
                                            
                                            # Set store name based on marketplace
                                            if store_info.get("marketplace") == "amazon":
                                                store_info["name"] = "Amazon.in"
                                            elif store_info.get("marketplace") == "apple":
                                                store_info["name"] = "Apple"
                                            elif store_info.get("marketplace") == "croma":
                                                store_info["name"] = "Croma"
                                            elif store_info.get("marketplace") == "flipkart":
                                                store_info["name"] = "Flipkart"
                                            elif store_info.get("marketplace") == "iplanet":
                                                store_info["name"] = "iPlanet"
                                            elif store_info.get("marketplace") == "macstation":
                                                store_info["name"] = "MacStation"
                                            elif store_info.get("marketplace") == "newunbox":
                                                store_info["name"] = "NewUnbox"
                                            elif store_info.get("marketplace") == "poorvika":
                                                store_info["name"] = "Poorvika"
                                            elif store_info.get("marketplace") == "quicktech":
                                                store_info["name"] = "QuickTech"
                                            elif store_info.get("marketplace") == "unicornstore":
                                                store_info["name"] = "Unicorn Store"
                                            elif store_info.get("marketplace") == "vijaysales":
                                                store_info["name"] = "Vijay Sales"
                                            elif store_info.get("marketplace") == "sathya":
                                                store_info["name"] = "Sathya"
                                            else:
                                                # Fallback to context-based name
                                                name_match = re.search(r'"name":"([^"]+)"', context)
                                                if name_match:
                                                    store_info["name"] = name_match.group(1)
                                            
                                            base_price_match = re.search(r'"basePrice":"([^"]+)"', context)
                                            if base_price_match:
                                                store_info["basePrice"] = base_price_match.group(1)
                                            
                                            total_price_match = re.search(r'"totalPrice":"([^"]+)"', context)
                                            if total_price_match:
                                                store_info["totalPrice"] = total_price_match.group(1)
                                            
                                            if store_info.get("marketplace"):
                                                store_key = f"{store_info['marketplace']}_{link}"
                                                if store_key not in seen_stores:
                                                    seen_stores.add(store_key)
                                                    stores_data.append(store_info)
                                
                                
                                if stores_data:
                                    product_header["stores"] = stores_data
                                
                                widgets_data.append(product_header)
                            
                            # Extract PRODUCT_DETAILS widget
                            sections_match = re.search(r'"sections":\s*(\[.*?\])', json_str)
                            if sections_match:
                                try:
                                    sections = json.loads(sections_match.group(1))
                                    widgets_data.append({
                                        "sections": sections,
                                        "type": "PRODUCT_DETAILS"
                                    })
                                except:
                                    # Manual extraction of sections
                                    sections_data = []
                                    
                                    # Extract SPECIFICATIONS section
                                    specs_match = re.search(r'"details":\s*(\[.*?\])', json_str)
                                    if specs_match:
                                        try:
                                            specs = json.loads(specs_match.group(1))
                                            sections_data.append({
                                                "details": specs,
                                                "sectionLabel": "Full Specs",
                                                "type": "SPECIFICATIONS"
                                            })
                                        except:
                                            # Manual extraction of specs
                                            spec_items = re.findall(r'\{"label":"([^"]+)","value":"([^"]+)"\}', json_str)
                                            if spec_items:
                                                sections_data.append({
                                                    "details": [{"label": label, "value": value} for label, value in spec_items],
                                                    "sectionLabel": "Full Specs",
                                                    "type": "SPECIFICATIONS"
                                                })
                                    
                                    # Extract REVIEWS section
                                    reviews_match = re.search(r'"detailedReviews":\s*(\[.*?\])', json_str)
                                    rating_match = re.search(r'"rating":\s*([0-9.]+)', json_str)
                                    review_count_match = re.search(r'"reviewsCount":\s*(\d+)', json_str)
                                    
                                    if reviews_match or rating_match or review_count_match:
                                        review_section = {
                                            "type": "REVIEWS",
                                            "sectionLabel": "Reviews",
                                            "rating": float(rating_match.group(1)) if rating_match else None,
                                            "reviewsCount": int(review_count_match.group(1)) if review_count_match else None,
                                            "detailedReviews": []
                                        }
                                        
                                        if reviews_match:
                                            try:
                                                review_section["detailedReviews"] = json.loads(reviews_match.group(1))
                                            except:
                                                pass
                                        
                                        sections_data.append(review_section)
                                    
                                    if sections_data:
                                        widgets_data.append({
                                            "sections": sections_data,
                                            "type": "PRODUCT_DETAILS"
                                        })
                            
                            # Extract PICKED_REASONS widget
                            highlights_match = re.search(r'"highlights":\s*(\[.*?\])', json_str)
                            score_match = re.search(r'"scoreData":\s*(\{.*?\})', json_str)
                            
                            if highlights_match or score_match:
                                picked_reasons = {
                                    "type": "PICKED_REASONS",
                                    "sectionLabel": "Why We Picked This",
                                    "showShimmer": False,
                                    "summary": [],
                                    "highlights": [],
                                    "scoreData": None
                                }
                                
                                if highlights_match:
                                    try:
                                        picked_reasons["highlights"] = json.loads(highlights_match.group(1))
                                    except:
                                        pass
                                
                                if score_match:
                                    try:
                                        picked_reasons["scoreData"] = json.loads(score_match.group(1))
                                    except:
                                        pass
                                
                                widgets_data.append(picked_reasons)
                            
                            # Extract REFINE_SEARCH widget
                            queries_match = re.search(r'"queries":\s*(\[.*?\])', json_str)
                            if queries_match:
                                try:
                                    queries = json.loads(queries_match.group(1))
                                    widgets_data.append({
                                        "queries": queries,
                                        "title": "Refine your search",
                                        "type": "REFINE_SEARCH"
                                    })
                                except:
                                    pass
                            
                            # Set widgets in initialData
                            if widgets_data:
                                extracted_data["initialData"]["widgets"] = widgets_data
                            
                            return json.dumps(extracted_data, indent=2, ensure_ascii=False)
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
    single_result = get_details_product("Y1U_RPVt")
    print(single_result)
