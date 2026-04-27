import os
import urllib.request
from playwright.sync_api import sync_playwright

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
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        print("Going to login page...")
        page.goto('https://octopus.energy/login/')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)

        # Print all inputs found
        inputs = page.locator('input').all()
        print(f"Found {len(inputs)} inputs")
        for i, inp in enumerate(inputs):
            print(f"Input {i}: type={inp.get_attribute('type')} name={inp.get_attribute('name')} placeholder={inp.get_attribute('placeholder')}")

        # Click the email field and type
        page.locator('input').nth(0).click()
        page.wait_for_timeout(500)
        page.keyboard.type(email)
        print("Typed email")

        # Click the password field and type
        page.locator('input').nth(1).click()
        page.wait_for_timeout(500)
        page.keyboard.type(password)
        print("Typed password")

        page.screenshot(path='screenshot_filled.png')

        # Press Enter to submit
        page.keyboard.press('Enter')
        page.wait_for_load_state('networkidle')
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
