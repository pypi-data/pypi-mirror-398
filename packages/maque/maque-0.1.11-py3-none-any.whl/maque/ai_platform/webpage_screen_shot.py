# pip install playwright
# playwright install

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from PIL import Image
from io import BytesIO
import traceback
from loguru import logger


class ScreenshotTaker:
    def __init__(self, viewport_width=1920, viewport_height=1080, max_concurrent_tasks=16, retry_limit=3):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.retry_limit = retry_limit  # Maximum retry attempts for loading a page
        self.browser = None
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)  # Limit concurrent tasks

    async def _initialize_browser(self):
        """Initialize the browser if not already done."""
        if self.browser is None:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True,
                                                                     args=['--disable-web-security'],  # Handle CORS
               )
            except Exception as e:
                logger.error(f"Failed to initialize browser: {e}")
                raise

    async def _load_page_with_retries(self, page, url):
        """Attempt to load a page with retries if it fails to load."""
        for attempt in range(self.retry_limit):
            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)  # Short timeout for quicker retries
                return True
            except (PlaywrightTimeoutError, Exception) as e:
                logger.warning(f"Attempt {attempt + 1} to load {url} failed: {e}")
                await asyncio.sleep(1.1)  # Wait briefly before retrying

        logger.error(f"Failed to load {url} after {self.retry_limit} attempts.")
        return False

    async def capture_screenshot_in_context(self, context, url, screenshot_path=None):
        """Capture a full-page screenshot of a single URL within a shared context."""
        async with self.semaphore:  # Limit concurrency
            try:
                # Open a new page in the shared context
                page = await context.new_page()

                # Attempt to load the page with retries
                if not await self._load_page_with_retries(page, url):
                    await page.close()
                    return None  # Skip screenshot if page load fails

                logger.debug(f"Loading {url}")
                # Scroll progressively to ensure lazy-loaded content is displayed
                # 滚动次数
                # scroll_height = await page.evaluate("document.body.scrollHeight")
                # viewport_height = await page.evaluate("window.innerHeight")
                # scroll_times = max(1, scroll_height // viewport_height)
                # logger.info(f"Scrolling {scroll_times} times")
                # for _ in range(scroll_times):
                #     await page.evaluate("""() => { window.scrollBy(0, window.innerHeight); }""")
                #     await asyncio.sleep(1/scroll_times)
                await page.evaluate("""() => { window.scrollTo(0, document.body.scrollHeight); }""")
                await asyncio.sleep(1.1)  # Allow time for content to load

                # Adjust iframe heights if present
                for iframe_element in await page.query_selector_all("iframe"):
                    try:
                        frame = await iframe_element.content_frame()
                        if frame:
                            logger.debug(f"Handling iframe in {url}")
                            frame_height = await frame.evaluate("document.body.scrollHeight")
                            await iframe_element.evaluate(f"el => el.style.height = '{frame_height}px'")
                            await asyncio.sleep(1.1)
                    except Exception as iframe_error:
                        logger.warning(f"Error handling iframe in {url}: {iframe_error}")

                # Capture and store screenshot as bytes
                screenshot_bytes = await page.screenshot(full_page=True)
                image = Image.open(BytesIO(screenshot_bytes))

                # Save screenshot if a path is specified
                if screenshot_path:
                    image.save(screenshot_path)
                    logger.info(f"Screenshot saved at {screenshot_path}")

                await page.close()  # Close page to release resources
                return image

            except Exception as e:
                logger.error(f"Unexpected error capturing screenshot for {url}: {e}")
                traceback.print_exc()
                return None  # Return None if an error occurs

    async def _capture_batch_screenshots(self, urls, screenshot_paths=None):
        """
        Capture screenshots for a batch of URLs within a single context.

        Parameters:
        - urls: list of URLs to capture
        - screenshot_paths: optional list of paths to save each screenshot.
                            If None, screenshots will not be saved to files.

        Returns:
        - List of PIL image objects for each URL.
        """
        await self._initialize_browser()
        screenshot_paths = screenshot_paths or [None] * len(urls)

        # Create a new context for this batch
        context = await self.browser.new_context(
            viewport={"width": self.viewport_width, "height": self.viewport_height}
        )

        # Execute all screenshot tasks within this context
        tasks = [self.capture_screenshot_in_context(context, url, path) for url, path in zip(urls, screenshot_paths)]
        images = await asyncio.gather(*tasks, return_exceptions=True)

        # Close context after batch is completed
        await context.close()

        # Filter out None or exceptions from results
        images = [img for img in images if isinstance(img, Image.Image)]
        return images

    async def capture_multi_screenshots(self, urls, batch_size=3, max_batches=3, screenshot_paths=None):
        """
        Capture screenshots for multiple URLs in multiple batches, with specified batch size and concurrency.

        Parameters:
        - urls: list of URLs to capture
        - batch_size: number of URLs per batch
        - max_batches: maximum number of concurrent batches
        - screenshot_paths: optional list of paths to save each screenshot.
                            If None, screenshots will not be saved to files.

        Returns:
        - List of PIL image objects for each URL.
        """
        await self._initialize_browser()
        screenshot_paths = screenshot_paths or [None] * len(urls)

        # Split URLs into batches
        url_batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]
        path_batches = [screenshot_paths[i:i + batch_size] for i in range(0, len(screenshot_paths), batch_size)]

        # Limit concurrent batch execution
        batch_semaphore = asyncio.Semaphore(max_batches)

        async def run_batch(urls, paths):
            async with batch_semaphore:
                return await self._capture_batch_screenshots(urls, paths)

        # Schedule all batch tasks
        tasks = [run_batch(url_batch, path_batch) for url_batch, path_batch in zip(url_batches, path_batches)]
        batch_images = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten the list of images from all batches and filter out None or exceptions
        images = [img for batch in batch_images if isinstance(batch, list) for img in batch]
        return images

    async def close(self):
        """Close the browser and Playwright if they are open."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if hasattr(self, 'playwright'):
            await self.playwright.stop()


if __name__ == "__main__":
    async def main():
        screenshot_taker = ScreenshotTaker()  # Limit concurrent requests
        url1 = "https://baidu.com"
        urls = [url1] * 20  # Example: large batch of URLs
        paths = [f"screenshot_{i}.png" for i in range(len(urls))]

        # Batch screenshot and get a list of PIL image objects
        images = await screenshot_taker.capture_multi_screenshots(urls,
                                                                  batch_size=3,
                                                                  max_batches=3,
                                                                  screenshot_paths=paths)

        # Close the browser
        await screenshot_taker.close()
        return images


    asyncio.run(main())


