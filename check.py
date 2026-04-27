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
        print("Logging in...")
        page.goto('https://octopus.energy/login/')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)

        # Fill email
        email_input = page.locator('input[type="email"], input[placeholder*="mail"], input[placeholder*="Email"]').first
        email_input.fill(email)
        print("Email filled")

        # Fill password
        password_input = page.locator('input[type="password"], input[placeholder*="assword"]').first
        password_input.fill(password)
        print("Password filled")

        page.screenshot(path='screenshot_before_submit.png')

        # Click sign in
        page.locator('button:has-text("Sign in"), input[type="submit"]').first.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)
        page.screenshot(path='screenshot_after_login.png')
        print("Clicked sign in")

        # Navigate to offer page
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
