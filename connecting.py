from patchright.sync_api import sync_playwright, Page

port = 58073

min_step_delay = 0.5
max_step_delay = 2.5

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
    print(f"Connected: {browser.is_connected()}")
    print(f"Contexts: {len(browser.contexts)}")

    _context = browser.contexts[0]
    # await _context.route("**/*", proxy_handler)
    _page_instance: Page

    if _context.pages:
        _page_instance = _context.pages[0]
    else:
        _page_instance = _context.new_page()

    a = _page_instance.locator('xpath=//input[@data-input-name="realName"]')
    print(a.input_value())

