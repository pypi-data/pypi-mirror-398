#!/usr/bin/env python3
"""
Playwright Browser Automation Utilities
Provides browser automation, testing, and scraping capabilities.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio


class PlaywrightUtils:
    """Browser automation and testing utilities using Playwright."""

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        slow_mo: int = 0,
        timeout: int = 30000,
    ):
        """
        Initialize Playwright utilities.

        Args:
            browser_type: Browser to use (chromium, firefox, webkit)
            headless: Run browser in headless mode
            slow_mo: Slow down operations by specified ms
            timeout: Default timeout in milliseconds
        """
        self.browser_type = browser_type
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start Playwright and browser."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Install with: pip install playwright && playwright install"
            )

        self.playwright = await async_playwright().start()

        # Get browser launcher
        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = await browser_launcher.launch(
            headless=self.headless, slow_mo=self.slow_mo
        )

        # Create context with default settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        self.context.set_default_timeout(self.timeout)

        return self

    async def close(self):
        """Close browser and Playwright."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def screenshot(
        self,
        url: str,
        output_path: str,
        full_page: bool = False,
        wait_for: Optional[str] = None,
    ) -> Path:
        """
        Take screenshot of a webpage.

        Args:
            url: URL to capture
            output_path: Path to save screenshot
            full_page: Capture full scrollable page
            wait_for: CSS selector to wait for before screenshot

        Returns:
            Path to saved screenshot
        """
        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")

            if wait_for:
                await page.wait_for_selector(wait_for)

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)

            await page.screenshot(path=str(output), full_page=full_page)
            print(f"✅ Screenshot saved: {output}")
            return output

        finally:
            await page.close()

    async def pdf(
        self,
        url: str,
        output_path: str,
        format: str = "A4",
        print_background: bool = True,
    ) -> Path:
        """
        Generate PDF from webpage.

        Args:
            url: URL to convert
            output_path: Path to save PDF
            format: Paper format (A4, Letter, etc.)
            print_background: Include background graphics

        Returns:
            Path to saved PDF
        """
        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)

            await page.pdf(
                path=str(output), format=format, print_background=print_background
            )
            print(f"✅ PDF saved: {output}")
            return output

        finally:
            await page.close()

    async def scrape(
        self, url: str, selectors: Dict[str, str], wait_for: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape content from webpage.

        Args:
            url: URL to scrape
            selectors: Dict of {name: css_selector}
            wait_for: CSS selector to wait for

        Returns:
            Dict of scraped content
        """
        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")

            if wait_for:
                await page.wait_for_selector(wait_for)

            results = {}
            for name, selector in selectors.items():
                elements = await page.query_selector_all(selector)
                results[name] = [
                    await elem.inner_text() for elem in elements if elem
                ]

            return results

        finally:
            await page.close()

    async def fill_form(
        self, url: str, form_data: Dict[str, str], submit_selector: Optional[str] = None
    ) -> bool:
        """
        Fill and optionally submit a form.

        Args:
            url: URL with form
            form_data: Dict of {selector: value}
            submit_selector: CSS selector for submit button

        Returns:
            True if successful
        """
        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")

            # Fill form fields
            for selector, value in form_data.items():
                await page.fill(selector, value)

            # Submit if requested
            if submit_selector:
                await page.click(submit_selector)
                await page.wait_for_load_state("networkidle")

            print("✅ Form filled successfully")
            return True

        finally:
            await page.close()

    async def click_sequence(
        self, url: str, selectors: List[str], wait_between: int = 1000
    ) -> bool:
        """
        Execute a sequence of clicks.

        Args:
            url: Starting URL
            selectors: List of CSS selectors to click in order
            wait_between: Milliseconds to wait between clicks

        Returns:
            True if successful
        """
        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")

            for selector in selectors:
                await page.wait_for_selector(selector)
                await page.click(selector)
                await page.wait_for_timeout(wait_between)

            print("✅ Click sequence completed")
            return True

        finally:
            await page.close()

    async def authenticate(self, url: str, username: str, password: str) -> bool:
        """
        Perform HTTP Basic Authentication.

        Args:
            url: URL requiring auth
            username: Username
            password: Password

        Returns:
            True if successful
        """
        await self.context.set_http_credentials(
            {"username": username, "password": password}
        )

        page = await self.context.new_page()

        try:
            response = await page.goto(url, wait_until="networkidle")
            success = response.status < 400
            print(f"{'✅' if success else '❌'} Authentication {'successful' if success else 'failed'}")
            return success

        finally:
            await page.close()

    async def emulate_device(self, device_name: str, url: str) -> Dict[str, Any]:
        """
        Emulate mobile device and capture page info.

        Args:
            device_name: Device to emulate (e.g., 'iPhone 12')
            url: URL to visit

        Returns:
            Page information
        """
        from playwright.async_api import devices

        if device_name not in devices:
            raise ValueError(f"Unknown device: {device_name}")

        # Create context with device settings
        device_context = await self.browser.new_context(**devices[device_name])
        page = await device_context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")

            info = {
                "url": page.url,
                "title": await page.title(),
                "viewport": device_context.viewport_size,
                "user_agent": await page.evaluate("navigator.userAgent"),
            }

            print(f"✅ Emulated {device_name}")
            return info

        finally:
            await page.close()
            await device_context.close()

    async def intercept_requests(
        self, url: str, route_handler: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Monitor and optionally intercept network requests.

        Args:
            url: URL to visit
            route_handler: Optional function to handle routes

        Returns:
            List of captured requests
        """
        page = await self.context.new_page()
        requests = []

        async def handle_request(request):
            requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "headers": request.headers,
                    "resource_type": request.resource_type,
                }
            )
            await request.continue_()

        await page.route("**/*", handle_request)

        try:
            await page.goto(url, wait_until="networkidle")
            print(f"✅ Captured {len(requests)} requests")
            return requests

        finally:
            await page.close()

    async def wait_for_element(
        self, url: str, selector: str, timeout: Optional[int] = None
    ) -> bool:
        """
        Wait for element to appear on page.

        Args:
            url: URL to visit
            selector: CSS selector to wait for
            timeout: Optional timeout override

        Returns:
            True if element appeared
        """
        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_selector(selector, timeout=timeout or self.timeout)
            print(f"✅ Element found: {selector}")
            return True

        except Exception as e:
            print(f"❌ Element not found: {selector} - {e}")
            return False

        finally:
            await page.close()

    async def execute_script(self, url: str, script: str) -> Any:
        """
        Execute JavaScript on page.

        Args:
            url: URL to visit
            script: JavaScript code to execute

        Returns:
            Script result
        """
        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle")
            result = await page.evaluate(script)
            print("✅ Script executed")
            return result

        finally:
            await page.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Browser automation with Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser type to use",
    )
    parser.add_argument(
        "--headed", action="store_true", help="Run browser in headed mode"
    )
    parser.add_argument(
        "--slow-mo", type=int, default=0, help="Slow down operations (ms)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Screenshot command
    screenshot_parser = subparsers.add_parser("screenshot", help="Capture screenshot")
    screenshot_parser.add_argument("url", help="URL to capture")
    screenshot_parser.add_argument("-o", "--output", required=True, help="Output path")
    screenshot_parser.add_argument(
        "--full-page", action="store_true", help="Capture full page"
    )
    screenshot_parser.add_argument("--wait-for", help="CSS selector to wait for")

    # PDF command
    pdf_parser = subparsers.add_parser("pdf", help="Generate PDF")
    pdf_parser.add_argument("url", help="URL to convert")
    pdf_parser.add_argument("-o", "--output", required=True, help="Output path")
    pdf_parser.add_argument("--format", default="A4", help="Paper format")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape content")
    scrape_parser.add_argument("url", help="URL to scrape")
    scrape_parser.add_argument(
        "-s", "--selector", action="append", help="name:selector pairs"
    )
    scrape_parser.add_argument("-o", "--output", help="Output JSON file")

    # Fill form command
    form_parser = subparsers.add_parser("fill-form", help="Fill form")
    form_parser.add_argument("url", help="URL with form")
    form_parser.add_argument("--data", required=True, help="JSON file with form data")
    form_parser.add_argument("--submit", help="Submit button selector")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    async def run():
        async with PlaywrightUtils(
            browser_type=args.browser,
            headless=not args.headed,
            slow_mo=args.slow_mo,
        ) as pw:
            if args.command == "screenshot":
                await pw.screenshot(
                    args.url, args.output, args.full_page, args.wait_for
                )

            elif args.command == "pdf":
                await pw.pdf(args.url, args.output, args.format)

            elif args.command == "scrape":
                selectors = {}
                if args.selector:
                    for sel in args.selector:
                        name, selector = sel.split(":", 1)
                        selectors[name] = selector

                result = await pw.scrape(args.url, selectors)

                if args.output:
                    with open(args.output, "w") as f:
                        json.dump(result, f, indent=2)
                    print(f"✅ Results saved to {args.output}")
                else:
                    print(json.dumps(result, indent=2))

            elif args.command == "fill-form":
                with open(args.data) as f:
                    form_data = json.load(f)
                await pw.fill_form(args.url, form_data, args.submit)

    asyncio.run(run())


if __name__ == "__main__":
    main()
