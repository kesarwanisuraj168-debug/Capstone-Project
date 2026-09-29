import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to web dashboard
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        
        # Click Dataset tab
        await page.click("button[data-view='dataset']")
        await page.wait_for_timeout(1000)
        
        # Check if Synthetic Generator card exists
        gen_btn = await page.query_selector("#btnGenSynth")
        assert gen_btn is not None, "btnGenSynth button not found"
        
        # Click Generate & Seed Database
        await gen_btn.click()
        await page.wait_for_timeout(2000)
        
        # Verify feedback message
        feedback = await page.inner_text("#synthFeedback")
        print("Feedback after generation:", feedback.encode("ascii", "replace").decode())
        assert "Successfully generated" in feedback, "Generation failed"
        
        # Take a screenshot
        await page.screenshot(path="screenshots/synthetic_generator_test.png", full_page=True)
        print("Screenshot saved to screenshots/synthetic_generator_test.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
