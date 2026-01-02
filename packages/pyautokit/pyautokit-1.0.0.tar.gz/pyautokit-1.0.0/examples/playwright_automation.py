#!/usr/bin/env python3
"""
Playwright Browser Automation Examples
Demonstrates various browser automation tasks.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyautokit.playwright_utils import PlaywrightUtils


async def example_screenshots():
    """Example: Capture screenshots of websites."""
    print("\n=== Screenshot Examples ===")

    async with PlaywrightUtils() as pw:
        # Basic screenshot
        await pw.screenshot(
            "https://example.com",
            "screenshots/example.png",
        )

        # Full page screenshot
        await pw.screenshot(
            "https://github.com",
            "screenshots/github-full.png",
            full_page=True,
        )

        # Wait for specific element before screenshot
        await pw.screenshot(
            "https://news.ycombinator.com",
            "screenshots/hn.png",
            wait_for=".storylink",
        )


async def example_pdf_generation():
    """Example: Generate PDFs from websites."""
    print("\n=== PDF Generation Examples ===")

    async with PlaywrightUtils() as pw:
        # Generate PDF in A4 format
        await pw.pdf(
            "https://example.com",
            "pdfs/example.pdf",
            format="A4",
        )

        # Generate PDF in Letter format
        await pw.pdf(
            "https://docs.python.org",
            "pdfs/python-docs.pdf",
            format="Letter",
            print_background=True,
        )


async def example_web_scraping():
    """Example: Scrape content from dynamic websites."""
    print("\n=== Web Scraping Examples ===")

    async with PlaywrightUtils() as pw:
        # Scrape Hacker News titles
        selectors = {
            "titles": ".titleline > a",
            "scores": ".score",
        }

        results = await pw.scrape(
            "https://news.ycombinator.com",
            selectors,
            wait_for=".titleline",
        )

        print(f"Found {len(results.get('titles', []))} stories")
        for i, title in enumerate(results.get("titles", [])[:5]):
            print(f"  {i+1}. {title}")


async def example_form_automation():
    """Example: Fill and submit forms."""
    print("\n=== Form Automation Examples ===")

    async with PlaywrightUtils() as pw:
        # Example: Fill a search form
        form_data = {
            "input[name='q']": "playwright python",
        }

        await pw.fill_form(
            "https://duckduckgo.com",
            form_data,
            submit_selector="button[type='submit']",
        )

        print("Search form submitted successfully!")


async def example_login_workflow():
    """Example: Automated login testing."""
    print("\n=== Login Workflow Example ===")

    async with PlaywrightUtils() as pw:
        # Navigate to login page
        # Fill login credentials
        # Submit form
        # Verify successful login

        form_data = {
            "#username": "testuser@example.com",
            "#password": "testpass123",
        }

        # This is a demo - replace with actual login URL
        print("Login workflow ready (replace URL with actual login page)")
        # await pw.fill_form(
        #     "https://your-app.com/login",
        #     form_data,
        #     submit_selector="#login-button"
        # )


async def example_click_sequence():
    """Example: Execute a sequence of clicks."""
    print("\n=== Click Sequence Example ===")

    async with PlaywrightUtils() as pw:
        # Navigate through multi-step form or wizard
        selectors = [
            "#step1-next",
            "#step2-next",
            "#step3-submit",
        ]

        # This is a demo - replace with actual URL
        print("Click sequence ready (replace URL with actual multi-step form)")
        # await pw.click_sequence(
        #     "https://your-app.com/wizard",
        #     selectors,
        #     wait_between=1000
        # )


async def example_mobile_emulation():
    """Example: Test mobile responsiveness."""
    print("\n=== Mobile Emulation Example ===")

    async with PlaywrightUtils() as pw:
        # Test site on iPhone 12
        info = await pw.emulate_device(
            "iPhone 12",
            "https://example.com",
        )

        print(f"Title: {info['title']}")
        print(f"Viewport: {info['viewport']}")
        print(f"User Agent: {info['user_agent'][:50]}...")

        # Could also test on other devices:
        # - iPhone 12 Pro
        # - iPad Pro
        # - Pixel 5
        # - Galaxy S9+


async def example_network_monitoring():
    """Example: Monitor network requests."""
    print("\n=== Network Monitoring Example ===")

    async with PlaywrightUtils() as pw:
        # Capture all requests made by page
        requests = await pw.intercept_requests("https://example.com")

        print(f"\nCaptured {len(requests)} requests:")
        for req in requests[:5]:  # Show first 5
            print(f"  {req['method']} {req['url'][:60]}... ({req['resource_type']})")


async def example_wait_for_content():
    """Example: Wait for dynamic content to load."""
    print("\n=== Wait for Content Example ===")

    async with PlaywrightUtils() as pw:
        # Wait for specific element to appear (useful for SPAs)
        success = await pw.wait_for_element(
            "https://example.com",
            ".loaded-content",
            timeout=10000,  # 10 seconds
        )

        if success:
            print("Content loaded successfully!")
        else:
            print("Timeout waiting for content")


async def example_javascript_execution():
    """Example: Execute custom JavaScript."""
    print("\n=== JavaScript Execution Example ===")

    async with PlaywrightUtils() as pw:
        # Get page information via JavaScript
        script = """
        () => {
            return {
                title: document.title,
                url: window.location.href,
                cookies: document.cookie,
                screenSize: `${window.screen.width}x${window.screen.height}`,
                viewportSize: `${window.innerWidth}x${window.innerHeight}`
            }
        }
        """

        result = await pw.execute_script("https://example.com", script)
        print(f"Page info: {result}")


async def example_authentication():
    """Example: HTTP Basic Authentication."""
    print("\n=== Authentication Example ===")

    async with PlaywrightUtils() as pw:
        # Authenticate to protected resource
        success = await pw.authenticate(
            "https://httpbin.org/basic-auth/user/pass",
            "user",
            "pass",
        )

        if success:
            print("Authentication successful!")
        else:
            print("Authentication failed")


async def example_multi_browser():
    """Example: Test across different browsers."""
    print("\n=== Multi-Browser Testing Example ===")

    browsers = ["chromium", "firefox", "webkit"]

    for browser_type in browsers:
        print(f"\nTesting with {browser_type}...")
        async with PlaywrightUtils(browser_type=browser_type) as pw:
            await pw.screenshot(
                "https://example.com",
                f"screenshots/example-{browser_type}.png",
            )
            print(f"✅ Screenshot saved for {browser_type}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PLAYWRIGHT BROWSER AUTOMATION EXAMPLES")
    print("=" * 60)

    # Create output directories
    Path("screenshots").mkdir(exist_ok=True)
    Path("pdfs").mkdir(exist_ok=True)

    # Run examples
    try:
        await example_screenshots()
        await example_pdf_generation()
        await example_web_scraping()
        await example_form_automation()
        await example_login_workflow()
        await example_click_sequence()
        await example_mobile_emulation()
        await example_network_monitoring()
        await example_wait_for_content()
        await example_javascript_execution()
        await example_authentication()
        await example_multi_browser()

    except ImportError as e:
        print("\n❌ Playwright not installed!")
        print("Install with: pip install 'pyautokit[browser]'")
        print("Then run: playwright install")
        return
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - screenshots/*.png")
    print("  - pdfs/*.pdf")
    print("\nNext steps:")
    print("  - Customize examples for your use case")
    print("  - Check pyautokit/playwright_utils.py for more methods")
    print("  - Run: pyautokit-browser --help")


if __name__ == "__main__":
    asyncio.run(main())
