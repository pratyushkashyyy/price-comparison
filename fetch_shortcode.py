from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
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
        browser = None
        context = None
        user_agent = get_random_user_agent()
        print(f"🌐 Using User Agent: {user_agent}")

        try:
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
            context.set_default_timeout(30000)
            context.set_default_navigation_timeout(60000)

            print(f"📄 Creating new page...")
            page = context.new_page()

            # URL encode the entire URL to handle query parameters properly
            import urllib.parse
            encoded_url = urllib.parse.quote(url, safe='')
            target_url = f"https://flash.co/{encoded_url}"
            print(f"🌐 Navigating to: {target_url}")
            navigation_start = datetime.now()
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            except PlaywrightTimeoutError:
                print(f"⏰ Navigation timed out after 60 seconds: {target_url}")
                return None
            navigation_duration = (datetime.now() - navigation_start).total_seconds()
            print(f"🌐 Navigation completed in {navigation_duration:.2f} seconds")

            print(f"🔄 Waiting for redirect to product-details...")
            redirect_start = datetime.now()
            redirect_attempts = 0
            max_attempts = 240  # 2 minutes at 500ms per attempt
            product_url = None

            while redirect_attempts < max_attempts:
                current_url = page.url

                # Only print every 5 attempts to reduce log spam, but always print on first few attempts
                if redirect_attempts <= 5 or redirect_attempts % 10 == 0:
                    print(f"🔄 Attempt {redirect_attempts}: Current URL: {current_url}")

                if "fallback" in current_url:
                    print(f"❌ No 'details' found in product_url: {current_url}")
                    return None

                # Check for different possible redirect patterns
                if "product-details" in current_url:
                    product_url = current_url
                    redirect_duration = (datetime.now() - redirect_start).total_seconds()
                    print(f"✅ Found product-details URL in {redirect_duration:.2f} seconds: {product_url}")
                    break
                page.wait_for_timeout(500)
                redirect_attempts += 1

            # If we exit the loop without finding product-details, handle timeout
            if not product_url:
                print(f"⏰ Timeout reached after {max_attempts} attempts, current URL: {page.url}")
                return None

            pageId = None
            if 'pageId=' in product_url:
                pageId = product_url.split('pageId=')[-1].split('&')[0]
                print(f"📱 Extracted pageId from pageId parameter: {pageId}")
            else:
                # Try to extract pageId from the URL path (e.g., /product-details/1VItfFCF/...)
                import re
                match = re.search(r'/product-details/([^/]+)', product_url)
                if match:
                    pageId = match.group(1)
                    print(f"📱 Extracted pageId from URL path: {pageId}")
                else:
                    print(f"❌ No pageId found in URL: {product_url}")

            total_duration = (datetime.now() - start_time).total_seconds()
            print(f"✅ get_shortcode completed in {total_duration:.2f} seconds, returning: {pageId}")
            return pageId
        except Exception as e:
            print(f"❌ get_shortcode failed for URL {url}: {e}")
            return None
        finally:
            print(f"🧹 Closing browser context and browser...")
            if context:
                context.close()
            if browser:
                browser.close()

if __name__ == "__main__":
    url = input("Enter the URL: ")
    print(get_shortcode(url))
