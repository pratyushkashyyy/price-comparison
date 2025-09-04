from playwright.sync_api import sync_playwright
import random
from datetime import datetime
from time import sleep

def get_random_user_agent():
    """Returns a random realistic user agent string"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    ]
    return random.choice(user_agents)

def get_shortcode(url):
    print(f"🌐 get_shortcode called with URL: {url}")
    start_time = datetime.now()
    
    with sync_playwright() as p:
        user_agent = get_random_user_agent()
        print(f"🌐 Using User Agent: {user_agent}")
        
        print(f"🚀 Launching browser...")
        browser_start = datetime.now()
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--memory-pressure-off',
                '--max_old_space_size=128' 
            ]
            )
        browser_duration = (datetime.now() - browser_start).total_seconds()
        print(f"🚀 Browser launched in {browser_duration:.2f} seconds")
        
        print(f"📄 Creating browser context...")
        context = browser.new_context(
            user_agent=user_agent,
            viewport={'width': 1920, 'height': 1080}
        )
        
        print(f"📄 Creating new page...")
        page = context.new_page()
        
        target_url = f"https://flash.co/{url}"
        print(f"🌐 Navigating to: {target_url}")
        navigation_start = datetime.now()
        page.goto(target_url)
        navigation_duration = (datetime.now() - navigation_start).total_seconds()
        print(f"🌐 Navigation completed in {navigation_duration:.2f} seconds")
        
        print(f"🔄 Waiting for redirect to product-details...")
        redirect_start = datetime.now()
        redirect_attempts = 0
        last_url = ""
        stuck_count = 0
        
        while True:
            redirect_attempts += 1
            current_url = page.url
            
            # Only print every 5 attempts to reduce log spam, but always print on first few attempts
            if redirect_attempts <= 5 or redirect_attempts % 10 == 0:
                print(f"🔄 Attempt {redirect_attempts}: Current URL: {current_url}")
            
            # Check for different possible redirect patterns
            if "product-details" in current_url:
                product_url = current_url
                redirect_duration = (datetime.now() - redirect_start).total_seconds()
                print(f"✅ Found product-details URL in {redirect_duration:.2f} seconds: {product_url}")
                break
            
            # Check if URL is changing (not stuck)
            if current_url != last_url:
                last_url = current_url
                stuck_count = 0
            else:
                stuck_count += 1
            
            sleep(1)
        
        print(f"🧹 Closing browser context and browser...")
        context.close()
        browser.close()
        
        # Initialize pageId to None
        pageId = None
        
        if "details" in product_url:
            final_url = product_url
            if 'pageId=' in final_url:
                pageId = final_url.split('pageId=')[-1]
                print(f"📱 Extracted pageId: {pageId}")
            else:
                print(f"❌ No pageId found in URL: {final_url}")
                pageId = None
        else:
            print(f"❌ No 'details' found in product_url: {product_url}")
            pageId = None

        total_duration = (datetime.now() - start_time).total_seconds()
        print(f"✅ get_shortcode completed in {total_duration:.2f} seconds, returning: {pageId}")
        return(pageId)

if __name__ == "__main__":
    url = input("Enter the URL: ")
    print(get_shortcode(url))