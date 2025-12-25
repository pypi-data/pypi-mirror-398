import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime
import re

async def h10_asin_keyword_download(h10_email, h10_password, session_path, helium10_url, asins, start_date, end_date, folder_path, headless = True):
    print(f"[{datetime.now()}] 🔄 Starting Helium 10 session check...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = None

        # Try to load saved session
        if os.path.exists(session_path):
            try:
                context = await browser.new_context(storage_state=session_path)
                print("✅ Loaded existing session.")
            except Exception as e:
                print(f"⚠️ Error loading session: {e}")
                context = await browser.new_context()
        else:
            context = await browser.new_context()
            print("🆕 No session found. Starting fresh...")
                
        page = await context.new_page()
        await page.goto(helium10_url)

        try:
            # Check if logged in
            await page.wait_for_selector("#h10-style-container > div.sc-bztcrM.dETACx > header > div.sc-AqqLW.dMCPUg > nav > ul > ul > li.sc-jOltFJ.fjjKvL > a > svg", timeout=90000)
            print("✅ Already logged in.")
        except:
            print("🔐 Not logged in. Attempting login...")

            # await page.goto("https://members.helium10.com/")
            await page.wait_for_selector("#loginform-email")
            await page.fill("#loginform-email", h10_email)
            await page.fill("#loginform-password", h10_password)
            await page.click("#login-form > button")

            # Wait for dashboard/redirect
            try:
                await page.wait_for_selector("#h10-style-container > div.sc-bztcrM.dETACx > header > div.sc-AqqLW.dMCPUg > nav > ul > ul > li.sc-jOltFJ.fjjKvL > a > svg", timeout=90000)
                print("✅ Login successful.")
                await context.storage_state(path=session_path)
                print("💾 Session saved to session.json")
            except:
                raise ValueError("❌ Login to H10 failed.")

        print(f"[{datetime.now()}] ✅ Session ready.")
        
        # Wait for the search bar
        await page.reload()
        await asyncio.sleep(3)
        await page.reload()
        await asyncio.sleep(3)
        await page.reload()
        await page.wait_for_selector("#table-search-input", timeout=180000)
        
        for asin in asins:
            try:
                try:
                    await page.locator("div").filter(has_text=re.compile(r"^1 ProductCustomizeExport Data\.\.\.Add ProductsOpen Walkthrough$")).locator("#table-search-input").click()
                    await page.locator("div").filter(has_text=re.compile(r"^1 ProductCustomizeExport Data\.\.\.Add ProductsOpen Walkthrough$")).locator("#table-search-input").press("ControlOrMeta+a")
                    await page.locator("div").filter(has_text=re.compile(r"^1 ProductCustomizeExport Data\.\.\.Add ProductsOpen Walkthrough$")).locator("#table-search-input").fill(asin)
                    print(f"Searching for ASIN: {asin}")
                    await asyncio.sleep(1)
                    await page.locator("div").filter(has_text=re.compile(r"^1 ProductCustomizeExport Data\.\.\.Add ProductsOpen Walkthrough$")).locator("#table-search-input").press("Enter")
                except:
                    await page.locator("#table-search-input").click()
                    await page.locator("#table-search-input").fill(asin)
                    print(f"Searching for ASIN: {asin}")
                    await asyncio.sleep(1)
                    await page.locator("#table-search-input").press("Enter")

                # Click the Keywords Dropdown button
                kw_drop_button = page.get_by_test_id("table-cell-actions").get_by_role("button").nth(1)
                await kw_drop_button.wait_for(state='visible',timeout=15000)
                await kw_drop_button.click()

                # Click the "History" button
                export_button = page.locator("#keyword-tracked-keywords_wrapper").get_by_role("button", name="Export Data...")
                await export_button.wait_for(state='visible', timeout=90000)
                await export_button.click()

                # Wait 1 second and click the first dropdown option
                await asyncio.sleep(1)
                await page.get_by_text("Historical Data").click()

                # Wait for popup to appear and fill date
                date_textbox = page.get_by_role("textbox", name="Select a date")
                await date_textbox.wait_for(state='visible', timeout=15000)
                await date_textbox.fill(f"{start_date} - {end_date}")
                await asyncio.sleep(1)
                print("Date filled in successfully.")

                # Click outside the date box and download
                await page.get_by_role("heading", name="Export Historical Data Select").click()

                # Wait for popup to close (indicates download triggered)
                async with page.expect_download(timeout=90000) as download_info:
                    await page.get_by_role("button", name="Export", exact=True).click()
                download = await download_info.value
                
                await download.save_as(os.path.join(folder_path, f"{asin}_report.csv"))
                print(f"{asin}_report.csv Downloaded successfully.")

            except Exception as e:
                print(f"Error processing ASIN {asin}: {e}")
                continue

            await asyncio.sleep(3)
        
        await browser.close()

        file_count = len([f for f in os.listdir(folder_path) if f.endswith('.csv')])
        done_message = (f"✅ Total of {file_count} ASINs processed successfully.")
        return done_message