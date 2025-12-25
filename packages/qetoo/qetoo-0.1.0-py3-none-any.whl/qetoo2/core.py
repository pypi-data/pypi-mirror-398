from playwright.sync_api import sync_playwright

def open_site(url: str):
    """
    Open a website in a visible Chromium browser.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(15000)
        browser.close()
