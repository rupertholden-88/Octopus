import os
import urllib.request
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth

email = os.environ['OCTOPUS_EMAIL']
password = os.environ['OCTOPUS_PASSWORD']
ntfy_topic = os.environ['NTFY_TOPIC']
url = 'https://octopus.energy/dashboard/new/accounts/A-5980A65B/octoplus/partner/offer-group/925'

def send_notification(title, message):
    req = urllib.request.Request(
        f'https://ntfy.sh/{ntfy_topic}',
        data=message.encode('utf-8'),
        headers={
            'Title': title,
            'Priority': 'urgent',
            'Tags': 'coffee,money',
        },
        method='POST'
    )
    urllib.request.urlopen(req)
    print(f"Notification sent: {title}")

with sync_playwright() as p:
    ci = os.environ.get('CI', '').lower() in ('1', 'true', 'yes')
    github_actions = os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'
    browser = p.chromium.launch(
        headless=ci or github_actions,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="Europe/London",
    )
    page = context.new_page()
    stealth(page)
    try:
        print("Going to login page...")
        page.goto('https://octopus.energy/login/', wait_until='domcontentloaded')
        page.wait_for_timeout(3000)

        try:
            page.click('button:has-text("Accept all"), button:has-text("Accept"), #onetrust-accept-btn-handler', timeout=3000)
            print("Accepted cookies")
            page.wait_for_timeout(1000)
        except Exception:
            print("No cookie consent dialog")

        # Print all inputs found
        inputs = page.locator('input').all()
        print(f"Found {len(inputs)} inputs")
        for i, inp in enumerate(inputs):
            print(f"Input {i}: type={inp.get_attribute('type')} name={inp.get_attribute('name')} placeholder={inp.get_attribute('placeholder')}")

        page.fill('input[type="email"]', email)
        print("Typed email")

        page.fill('input[type="password"]', password)
        print("Typed password")

        page.screenshot(path='screenshot_filled.png')

        page.click('button[type="submit"]')
        try:
            page.wait_for_url(lambda u: 'login' not in u, timeout=10000)
        except Exception:
            page.wait_for_timeout(4000)

        page.screenshot(path='screenshot_after_login.png')
        print(f"After login URL: {page.url}")

        if 'login' in page.url:
            print("Still on login page - login failed")
        else:
            print("Login succeeded, going to offer page...")
            page.goto(url)
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(3000)
            page.screenshot(path='screenshot.png')

            content = page.content().lower()
            print(f"Content length: {len(content)}")

            positive = ['claim', 'get your code', 'redeem', 'voucher', 'code available', 'cafe nero', 'caffe nero']
            negative = ['no codes', 'check back', 'come back', 'not available', 'all gone', 'none available', 'no reward']
            found_positive = any(kw in content for kw in positive)
            found_negative = any(kw in content for kw in negative)
            print(f"Positive: {found_positive}, Negative: {found_negative}")

            if found_positive and not found_negative:
                send_notification('☕ Cafe Nero Code Available!', 'Quick! Open the Octopus app now!')
            else:
                print("No code available")

    except Exception as e:
        print(f"Error: {e}")
        page.screenshot(path='screenshot.png')
    finally:
        browser.close()
