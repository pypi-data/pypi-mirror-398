import asyncio

from aiolimiter.compat import wait_for
from crawl4ai import AsyncWebCrawler, CacheMode


async def capture_and_save_screenshot(url: str, output_path: str):
    async with AsyncWebCrawler(verbose=True, headless=False) as crawler:
        result = await crawler.arun(
            url=url,
            # screenshot=True,
            cache_mode=CacheMode.BYPASS,

            # magic=True, # 当使用magic模式时,就不用设置下面两行

            simulate_user=True,  # Causes random mouse movements and clicks
            override_navigator=True,  # Makes the browser appear more like a real user

            # include_links_on_markdown=False,

            remove_overlay_elements=True,  # Remove popups/modals
            page_timeout=60000,  # Increased timeout for protection checks
            # wait_for="css:.content-loaded",


            excluded_tags=['nav', 'footer'],

        )
        print(result.markdown)
        # print(result.fit_markdown)

        if result.success and result.screenshot:
            import base64
            screenshot_data = base64.b64decode(result.screenshot)
            with open(output_path, "wb") as f:
                f.write(screenshot_data)
            print(f"Screenshot saved successfully to {output_path}")
        else:
            print("Failed to capture screenshot")


if __name__ == "__main__":
    # asyncio.run(capture_and_save_screenshot("https://www.gradio.app/guides/object-detection-from-video", "screenshot.png"))
    # asyncio.run(capture_and_save_screenshot("https://www.autohome.com.cn", "screenshot.png"))
    asyncio.run(capture_and_save_screenshot("https://www.zhihu.com/question/654186093/answer/3483543427", "screenshot.png"))
