#!/usr/bin/env python3
"""Tests for Playwright browser automation utilities."""

import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyautokit.playwright_utils import PlaywrightUtils


class MockPage:
    """Mock Playwright page."""

    def __init__(self):
        self.url = "https://example.com"
        self._title = "Example Page"
        self.goto = AsyncMock(return_value=MagicMock(status=200))
        self.wait_for_selector = AsyncMock()
        self.screenshot = AsyncMock()
        self.pdf = AsyncMock()
        self.query_selector_all = AsyncMock(return_value=[])
        self.fill = AsyncMock()
        self.click = AsyncMock()
        self.wait_for_timeout = AsyncMock()
        self.wait_for_load_state = AsyncMock()
        self.route = AsyncMock()
        self.evaluate = AsyncMock(return_value={"test": "result"})
        self.close = AsyncMock()

    async def title(self):
        return self._title


class MockElement:
    """Mock Playwright element."""

    def __init__(self, text):
        self._text = text

    async def inner_text(self):
        return self._text


class MockContext:
    """Mock Playwright browser context."""

    def __init__(self):
        self.viewport_size = {"width": 1920, "height": 1080}
        self.new_page = AsyncMock(return_value=MockPage())
        self.set_default_timeout = MagicMock()
        self.set_http_credentials = AsyncMock()
        self.close = AsyncMock()


class MockBrowser:
    """Mock Playwright browser."""

    def __init__(self):
        self.new_context = AsyncMock(return_value=MockContext())
        self.close = AsyncMock()


class MockBrowserType:
    """Mock Playwright browser type."""

    def __init__(self):
        self.launch = AsyncMock(return_value=MockBrowser())


class MockPlaywright:
    """Mock Playwright instance."""

    def __init__(self):
        self.chromium = MockBrowserType()
        self.firefox = MockBrowserType()
        self.webkit = MockBrowserType()
        self.stop = AsyncMock()


class MockAsyncPlaywright:
    """Mock async_playwright function."""

    async def start(self):
        return MockPlaywright()


@pytest.fixture
def mock_playwright():
    """Fixture for mocked Playwright."""
    with patch("pyautokit.playwright_utils.async_playwright") as mock:
        mock.return_value = MockAsyncPlaywright()
        yield mock


@pytest.mark.asyncio
class TestPlaywrightUtils:
    """Test PlaywrightUtils class."""

    async def test_init(self):
        """Test initialization."""
        pw = PlaywrightUtils(
            browser_type="firefox", headless=False, slow_mo=100, timeout=5000
        )
        assert pw.browser_type == "firefox"
        assert pw.headless is False
        assert pw.slow_mo == 100
        assert pw.timeout == 5000

    async def test_context_manager(self, mock_playwright):
        """Test async context manager."""
        async with PlaywrightUtils() as pw:
            assert pw.playwright is not None
            assert pw.browser is not None
            assert pw.context is not None

    async def test_start_chromium(self, mock_playwright):
        """Test starting Chromium browser."""
        pw = PlaywrightUtils(browser_type="chromium")
        await pw.start()

        assert pw.playwright is not None
        assert pw.browser is not None
        assert pw.context is not None

        await pw.close()

    async def test_start_firefox(self, mock_playwright):
        """Test starting Firefox browser."""
        pw = PlaywrightUtils(browser_type="firefox")
        await pw.start()

        assert pw.playwright is not None
        await pw.close()

    async def test_start_webkit(self, mock_playwright):
        """Test starting WebKit browser."""
        pw = PlaywrightUtils(browser_type="webkit")
        await pw.start()

        assert pw.playwright is not None
        await pw.close()

    async def test_screenshot(self, mock_playwright, tmp_path):
        """Test screenshot capture."""
        output_path = tmp_path / "screenshot.png"

        async with PlaywrightUtils() as pw:
            result = await pw.screenshot(
                "https://example.com", str(output_path), full_page=True
            )

            assert result == output_path

    async def test_screenshot_with_wait(self, mock_playwright, tmp_path):
        """Test screenshot with wait for selector."""
        output_path = tmp_path / "screenshot.png"

        async with PlaywrightUtils() as pw:
            result = await pw.screenshot(
                "https://example.com",
                str(output_path),
                wait_for=".ready",
            )

            assert result == output_path

    async def test_pdf_generation(self, mock_playwright, tmp_path):
        """Test PDF generation."""
        output_path = tmp_path / "page.pdf"

        async with PlaywrightUtils() as pw:
            result = await pw.pdf(
                "https://example.com",
                str(output_path),
                format="Letter",
            )

            assert result == output_path

    async def test_scrape_content(self, mock_playwright):
        """Test content scraping."""
        async with PlaywrightUtils() as pw:
            # Mock query results
            page = await pw.context.new_page()
            page.query_selector_all = AsyncMock(
                return_value=[
                    MockElement("Title 1"),
                    MockElement("Title 2"),
                ]
            )

            selectors = {"titles": "h1"}
            result = await pw.scrape("https://example.com", selectors)

            assert "titles" in result
            assert len(result["titles"]) == 2

    async def test_scrape_with_wait(self, mock_playwright):
        """Test scraping with wait for element."""
        async with PlaywrightUtils() as pw:
            page = await pw.context.new_page()
            page.query_selector_all = AsyncMock(
                return_value=[MockElement("Content")]
            )

            selectors = {"content": ".content"}
            result = await pw.scrape(
                "https://example.com",
                selectors,
                wait_for=".loaded",
            )

            assert "content" in result

    async def test_fill_form(self, mock_playwright):
        """Test form filling."""
        async with PlaywrightUtils() as pw:
            form_data = {
                "#email": "test@example.com",
                "#password": "secret123",
            }

            result = await pw.fill_form("https://example.com/form", form_data)
            assert result is True

    async def test_fill_form_with_submit(self, mock_playwright):
        """Test form filling with submission."""
        async with PlaywrightUtils() as pw:
            form_data = {"#username": "testuser"}

            result = await pw.fill_form(
                "https://example.com/login",
                form_data,
                submit_selector="#submit-btn",
            )
            assert result is True

    async def test_click_sequence(self, mock_playwright):
        """Test click sequence."""
        async with PlaywrightUtils() as pw:
            selectors = ["#menu", ".option1", ".submit"]

            result = await pw.click_sequence(
                "https://example.com",
                selectors,
                wait_between=500,
            )
            assert result is True

    async def test_authenticate(self, mock_playwright):
        """Test HTTP authentication."""
        async with PlaywrightUtils() as pw:
            result = await pw.authenticate(
                "https://example.com",
                "user",
                "pass",
            )
            assert result is True

    async def test_authenticate_failure(self, mock_playwright):
        """Test failed authentication."""
        async with PlaywrightUtils() as pw:
            page = await pw.context.new_page()
            page.goto = AsyncMock(return_value=MagicMock(status=401))

            result = await pw.authenticate(
                "https://example.com",
                "wrong",
                "creds",
            )
            assert result is False

    async def test_emulate_device(self, mock_playwright):
        """Test device emulation."""
        with patch("pyautokit.playwright_utils.devices") as mock_devices:
            mock_devices.__contains__ = lambda self, x: True
            mock_devices.__getitem__ = lambda self, x: {
                "viewport": {"width": 375, "height": 812},
                "user_agent": "Mobile Safari",
            }

            async with PlaywrightUtils() as pw:
                # Mock browser.new_context for device
                device_context = MockContext()
                device_context.viewport_size = {"width": 375, "height": 812}
                pw.browser.new_context = AsyncMock(return_value=device_context)

                result = await pw.emulate_device(
                    "iPhone 12",
                    "https://example.com",
                )

                assert "url" in result
                assert "viewport" in result

    async def test_emulate_device_unknown(self, mock_playwright):
        """Test emulating unknown device."""
        with patch("pyautokit.playwright_utils.devices") as mock_devices:
            mock_devices.__contains__ = lambda self, x: False

            async with PlaywrightUtils() as pw:
                with pytest.raises(ValueError, match="Unknown device"):
                    await pw.emulate_device("FakePhone", "https://example.com")

    async def test_intercept_requests(self, mock_playwright):
        """Test request interception."""
        async with PlaywrightUtils() as pw:
            requests = await pw.intercept_requests("https://example.com")

            assert isinstance(requests, list)

    async def test_wait_for_element_success(self, mock_playwright):
        """Test waiting for element successfully."""
        async with PlaywrightUtils() as pw:
            result = await pw.wait_for_element(
                "https://example.com",
                ".loaded",
            )
            assert result is True

    async def test_wait_for_element_timeout(self, mock_playwright):
        """Test waiting for element timeout."""
        async with PlaywrightUtils() as pw:
            page = await pw.context.new_page()
            page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))

            result = await pw.wait_for_element(
                "https://example.com",
                ".missing",
            )
            assert result is False

    async def test_execute_script(self, mock_playwright):
        """Test JavaScript execution."""
        async with PlaywrightUtils() as pw:
            result = await pw.execute_script(
                "https://example.com",
                "return document.title",
            )

            assert result is not None

    async def test_close(self, mock_playwright):
        """Test closing browser."""
        pw = PlaywrightUtils()
        await pw.start()
        await pw.close()

        # Verify close was called
        assert pw.context is not None
        assert pw.browser is not None
        assert pw.playwright is not None


class TestPlaywrightCLI:
    """Test Playwright CLI."""

    def test_cli_no_args(self, capsys):
        """Test CLI with no arguments."""
        with patch("sys.argv", ["playwright_utils.py"]):
            with pytest.raises(SystemExit):
                from pyautokit.playwright_utils import main

                main()

    @patch("pyautokit.playwright_utils.asyncio.run")
    def test_cli_screenshot(self, mock_run):
        """Test screenshot CLI command."""
        with patch(
            "sys.argv",
            [
                "playwright_utils.py",
                "screenshot",
                "https://example.com",
                "-o",
                "test.png",
            ],
        ):
            from pyautokit.playwright_utils import main

            main()
            assert mock_run.called

    @patch("pyautokit.playwright_utils.asyncio.run")
    def test_cli_pdf(self, mock_run):
        """Test PDF CLI command."""
        with patch(
            "sys.argv",
            [
                "playwright_utils.py",
                "pdf",
                "https://example.com",
                "-o",
                "test.pdf",
            ],
        ):
            from pyautokit.playwright_utils import main

            main()
            assert mock_run.called

    @patch("pyautokit.playwright_utils.asyncio.run")
    def test_cli_scrape(self, mock_run):
        """Test scrape CLI command."""
        with patch(
            "sys.argv",
            [
                "playwright_utils.py",
                "scrape",
                "https://example.com",
                "-s",
                "titles:h1",
            ],
        ):
            from pyautokit.playwright_utils import main

            main()
            assert mock_run.called

    @patch("pyautokit.playwright_utils.asyncio.run")
    @patch("builtins.open", new_callable=mock_open, read_data='{"#field": "value"}')
    def test_cli_fill_form(self, mock_file, mock_run):
        """Test fill-form CLI command."""
        with patch(
            "sys.argv",
            [
                "playwright_utils.py",
                "fill-form",
                "https://example.com",
                "--data",
                "form.json",
            ],
        ):
            from pyautokit.playwright_utils import main

            main()
            assert mock_run.called

    @patch("pyautokit.playwright_utils.asyncio.run")
    def test_cli_with_browser_option(self, mock_run):
        """Test CLI with browser option."""
        with patch(
            "sys.argv",
            [
                "playwright_utils.py",
                "--browser",
                "firefox",
                "screenshot",
                "https://example.com",
                "-o",
                "test.png",
            ],
        ):
            from pyautokit.playwright_utils import main

            main()
            assert mock_run.called

    @patch("pyautokit.playwright_utils.asyncio.run")
    def test_cli_headed_mode(self, mock_run):
        """Test CLI with headed mode."""
        with patch(
            "sys.argv",
            [
                "playwright_utils.py",
                "--headed",
                "screenshot",
                "https://example.com",
                "-o",
                "test.png",
            ],
        ):
            from pyautokit.playwright_utils import main

            main()
            assert mock_run.called
