from playwright.sync_api import Page, expect, sync_playwright
import pandas as pd
from datetime import datetime

data_list = []
failed_ids = []
perma_failed = []

def scrape_id(page, id, data_list):
    page.goto(f"https://admin.shopify.com/store/mr-roses-ro/apps/better-shipping/shipping_rate/{id}/edit", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    frame = page.frame_locator("iframe[name='app-iframe']")
    frame.locator("#shipping-rate-name-div").wait_for(state="visible", timeout=10000)
    shipping_name = (frame.locator("input[placeholder='E.g. USA Shipping']").input_value()).strip()

    next_button = frame.locator("#shipping-zone-next-button")
    next_button.wait_for(state="visible", timeout=10000)
    next_button.scroll_into_view_if_needed()
    page.wait_for_timeout(500)

    for click_attempt in range(3):
        next_button.click()
        try:
            page.wait_for_load_state("load", timeout=5000)
            page.wait_for_timeout(2000)
            break
        except:
            print(f"Next button click attempt {click_attempt + 1} didn't trigger load, retrying...")
            page.wait_for_timeout(1000)

    frame = page.frame_locator("iframe[name='app-iframe']")
    frame.locator("#include_exact_zip_code_input").wait_for(state="visible", timeout=60000)
    page.wait_for_timeout(60000)
    postcode = (frame.locator("#include_exact_zip_code_input").input_value()).strip()
    page.wait_for_timeout(2000)

    page.goto(f"https://admin.shopify.com/store/mr-roses-ro/apps/better-shipping/shipping_rates/{id}/shipping_rules", wait_until="domcontentloaded")
    page.wait_for_timeout(10000)

    frame = page.frame_locator("iframe[name='app-iframe']")
    frame.locator("#shipping_rules_table").wait_for(state="visible",timeout= 10000)
    page.wait_for_timeout(6000)
    rows_count = frame.locator("tr.shipping_rule_table_row").count()
    page.wait_for_load_state("domcontentloaded", timeout=15000)

    for idx in range(rows_count):
        row = frame.locator("tr.shipping_rule_table_row").nth(idx)
        rule_name = (row.locator("td.name_column").first.text_content() or "").strip()
        change = (row.locator("td.change_shipping_rate_name_column").first.text_content() or "").strip()
        price = (row.locator(".effect_value_column_div").first.text_content() or "").strip()
        page.wait_for_timeout(2000)

        if idx == 1:
            row.locator("td.name_column a.shipping_rules_index_link").first.click(force=True)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_timeout(2000)

            frame = page.frame_locator("iframe[name='app-iframe']")
            select_element = frame.locator("select[name='duallistbox_include_exclude_products_helper2']")
            select_element.wait_for(state='visible', timeout=10000)

            options = select_element.locator("option")
            options_count = options.count()
            rules_list = [
                options.nth(i).text_content()
                for i in range(options_count)
                if options.nth(i).text_content()
            ]
            rules = (','.join(rules_list)).strip()
        else:
            rules = (row.locator("td.type_column").first.text_content() or "").strip()

        
        data_list.append({
            "id": id,
            "shippingname": shipping_name,
            "postcodes": postcode,
            "rulename": rule_name,
            "rules": rules,
            "change": change,
            "price": price
        })

        page.wait_for_timeout(2000)


with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="user_data",
        headless=False,
        channel="chrome",
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.new_page()
    
    page.goto("https://admin.shopify.com/store/mr-roses-ro/apps/better-shipping/shipping_rate", wait_until='networkidle')
    page.wait_for_timeout(4000)

    frame = page.frame_locator("iframe[name='app-iframe']")
    page_numbers = frame.locator("div.pagination ul.pagination li a[data-turbo='false']").evaluate_all(
        """elements => elements
            .map(el => el.textContent.trim())
            .filter(text => /^\\d+$/.test(text))
            .map(Number)
        """
    )
    page_numbers = sorted(set(page_numbers))
    if not page_numbers or page_numbers[0] != 1:
        page_numbers = [1] + page_numbers

    id_values = []
    print(page_numbers)

    for page_num in page_numbers:
        if page_num == 1:
            frame = page.frame_locator("iframe[name='app-iframe']")
        else:
            page.goto(
                f"https://admin.shopify.com/store/mr-roses-ro/apps/better-shipping/shipping_rate?enabled_rates_page={page_num}",
                wait_until="networkidle",
            )
            page.wait_for_timeout(6000)
            frame = page.frame_locator("iframe[name='app-iframe']")

        rows = frame.locator("#shipping_rate_enabled_table tbody tr").all()
        for row in rows:
            row_id = row.get_attribute('id')
            if row_id:
                id_values.append(row_id)
        page.wait_for_timeout(2000)

    print(f"Total IDs collected: {len(id_values)}")

    for id in id_values:
        max_retries = 2
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            try:
                scrape_id(page, id, data_list)
                success = True
            except Exception as e:
                attempt += 1
                if attempt < max_retries:
                    print(f"ID {id} failed (attempt {attempt}), retrying... Error: {e}")
                    page.wait_for_timeout(3000)
                else:
                    print(f"ID {id} failed after {max_retries} attempts, skipping. Error: {e}")
                    failed_ids.append(id)

    # Retry failed IDs once more (no retry loop this time, just one attempt)
    if failed_ids:
        print(f"Retrying {len(failed_ids)} failed IDs...")
        for id in failed_ids:
            try:
                scrape_id(page, id, data_list)
            except Exception as e:
                perma_failed.append({
                    "failed to process id":id
                })
                print(f"ID {id} permanently failed: {e}")

    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    df = pd.DataFrame(data_list)
    csv_filename = f"Postcodes_{formatted_time}.csv"
    df.to_csv(csv_filename, index=True)
    print(f"Saved: {csv_filename} with {len(data_list)} rows")

    fd = pd.DataFrame(perma_failed)
    failed_csv = f"Failedcodes_{formatted_time}.csv"
    fd.to_csv(failed_csv,index=True) 
    print(f"Saved: {failed_csv} with {len(perma_failed)} rows")
    page.wait_for_timeout(3000)
    context.close()