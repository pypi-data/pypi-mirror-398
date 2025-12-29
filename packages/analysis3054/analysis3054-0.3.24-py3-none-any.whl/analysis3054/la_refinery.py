"""Utilities for downloading the Louisiana refinery activity report."""

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List

import pandas as pd
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout, async_playwright

# Configure logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("LA_Refinery_Scraper")

# Track whether we have already attempted to install Playwright browsers in this process
_PLAYWRIGHT_INSTALL_ATTEMPTED = False


class ScraperError(Exception):
    """Custom exception for scraping failures."""


async def safe_click(page: Page, selector_strategies: List[str], element_name: str) -> bool:
    """Attempts to click an element using a list of fallback selectors."""

    for selector in selector_strategies:
        try:
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=5000)
            await element.scroll_into_view_if_needed()
            await element.click()
            logger.debug("Clicked '%s' using selector: %s", element_name, selector)
            return True
        except Exception:
            logger.debug("Strategy failed for '%s': %s", element_name, selector)
            continue

    logger.error("Failed to click '%s' after trying all strategies.", element_name)
    return False


async def safe_fill(page: Page, selector_strategies: List[str], value: str, element_name: str) -> bool:
    """Attempts to fill an input field using a list of fallback selectors."""

    for selector in selector_strategies:
        try:
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=5000)
            await element.fill(value)
            await element.press("Tab")  # Trigger 'change' events
            logger.debug("Filled '%s' using selector: %s", element_name, selector)
            return True
        except Exception:
            continue

    logger.error("Failed to fill '%s' after trying all strategies.", element_name)
    return False


async def wait_for_apex_processing(page: Page):
    """Specific handler for Oracle APEX 'Processing' overlays."""

    try:
        try:
            await page.wait_for_selector(".u-Processing", state="visible", timeout=2000)
        except PlaywrightTimeout:
            pass  # Spinner might not have appeared, which is fine

        await page.wait_for_selector(".u-Processing", state="detached", timeout=30000)
    except Exception:
        # Fallback to generic network idle
        await page.wait_for_load_state("networkidle")


def _iter_browser_launchers(playwright):
    """Yield browser launch callables in preferred order."""

    def chromium_channel(channel_name):
        return lambda: playwright.chromium.launch(headless=True, channel=channel_name)

    yield chromium_channel("chrome")
    yield chromium_channel("msedge")
    yield lambda: playwright.webkit.launch(headless=True)
    # Fallbacks if preferred channels are unavailable
    yield lambda: playwright.chromium.launch(headless=True)
    yield lambda: playwright.webkit.launch(headless=True)


def _install_playwright_browsers() -> bool:
    """Install Playwright-managed browsers if they are missing.

    Returns:
        bool: True if an install was attempted in this process, False otherwise.
    """

    global _PLAYWRIGHT_INSTALL_ATTEMPTED
    if _PLAYWRIGHT_INSTALL_ATTEMPTED:
        return False

    _PLAYWRIGHT_INSTALL_ATTEMPTED = True
    try:
        import sys
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "playwright",
                "install",
                "chromium",
                "msedge",
                "webkit",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.info("Playwright browsers are installed or already present.")
        else:  # pragma: no cover - dependent on environment
            logger.warning(
                "Playwright browser installation returned non-zero exit %s: %s",
                result.returncode,
                (result.stderr or result.stdout).strip(),
            )
    except FileNotFoundError:  # pragma: no cover - environment specific
        logger.error("Playwright CLI is unavailable; cannot install browsers automatically.")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unexpected error while installing Playwright browsers: %s", exc)

    return True


async def fetch_la_refinery_data(start_date: str = "01-JAN-2018") -> pd.DataFrame:
    """
    Scrapes the LA DNR SONRIS Data Portal for Refinery Activity Reports.

    Args:
        start_date: Date string in 'DD-MON-YYYY' format (e.g., '01-JAN-2018').

    Returns:
        pd.DataFrame: The resulting dataset.

    Raises:
        ScraperError: If the scraping process fails at any critical step.
    """

    url = (
        "https://sonlite.dnr.state.la.us/ords/r/sonris_pub/sonris_data_portal/"
        "r3-activity-report-product-listing?clear=2466"
    )

    # Ensure Playwright-managed browser binaries are present before attempting to launch
    _install_playwright_browsers()

    # Create a temporary directory for the download to ensure thread safety and cleanliness
    with tempfile.TemporaryDirectory() as temp_dir:
        async with async_playwright() as p:
            browser = None
            context = None
            # Attempt preferred browsers in order: Chrome, Edge, Safari/WebKit, Chromium fallback
            for launcher in _iter_browser_launchers(p):
                try:
                    browser = await launcher()
                    break
                except Exception as exc:  # pragma: no cover - dependent on environment
                    logger.info("Browser launch failed, trying next option: %s", exc)
                    continue

            if browser is None:
                raise ScraperError(
                    "Unable to launch any supported browser (Chrome, Edge, Safari/WebKit)."
                )

            context = await browser.new_context(
                accept_downloads=True,
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                logger.info("Navigating to %s", url)
                await page.goto(url, timeout=60000)

                # 1. Set Date
                logger.info("Setting report date to %s", start_date)
                date_selectors = [
                    "input[aria-label='Begin Report Date']",
                    "label:has-text('Begin Report Date') >> .. >> input",
                    ".datepicker",
                ]
                if not await safe_fill(page, date_selectors, start_date, "Begin Date Input"):
                    raise ScraperError("Could not locate Date Input field.")

                # 2. Execute Report
                logger.info("Executing report generation")
                execute_selectors = [
                    "button:has-text('Execute')",
                    ".t-Button--hot",
                    "[id*='EXECUTE']",
                ]
                if not await safe_click(page, execute_selectors, "Execute Button"):
                    raise ScraperError("Could not click Execute button.")

                # 3. Wait for Grid Refresh
                await wait_for_apex_processing(page)
                # Extra buffer for table rendering
                await page.wait_for_timeout(2000)

                # 4. Open Actions Menu
                logger.info("Opening Actions menu")
                actions_selectors = [
                    "button:has-text('Actions')",
                    ".a-IRR-actions-button",
                    "[id$='_actions_button']",
                ]
                if not await safe_click(page, actions_selectors, "Actions Button"):
                    raise ScraperError("Could not open Actions menu.")

                # 5. Select Download
                logger.info("Selecting Download option")
                download_menu_selectors = [
                    "menuitem:has-text('Download')",
                    "div.a-Menu-content >> text='Download'",
                ]
                if not await safe_click(page, download_menu_selectors, "Download Menu Item"):
                    raise ScraperError("Could not find Download option in menu.")

                # 6. Trigger CSV Download
                logger.info("Initiating CSV download")
                async with page.expect_download() as download_info:
                    csv_selectors = [
                        "button:has-text('CSV')",
                        "label:has-text('CSV')",
                        ".a-IRR-dialog-content >> text='CSV'",
                    ]
                    if not await safe_click(page, csv_selectors, "CSV Format Button"):
                        raise ScraperError("Could not click CSV format button.")

                download = await download_info.value
                target_path = Path(temp_dir) / "data.csv"
                await download.save_as(target_path)

                logger.info("File downloaded successfully to %s", target_path)

                # 7. Parse Data
                # Check if file is empty
                if target_path.stat().st_size == 0:
                    raise ScraperError("Downloaded CSV file is empty.")

                df = pd.read_csv(target_path)
                logger.info("Successfully loaded DataFrame with %s rows.", len(df))

                return df

            except Exception as exc:
                logger.error("Scraping failed: %s", exc)
                # Take screenshot on failure for debugging (optional, saves to local dir)
                try:
                    await page.screenshot(path="error_screenshot.png")
                    logger.info("Error screenshot saved to 'error_screenshot.png'")
                except Exception:
                    pass
                raise
            finally:
                if context is not None:
                    await context.close()
                if browser is not None:
                    await browser.close()


# Wrapper to run the async function from synchronous code if needed
def LA_refinery(start_date: str = "01-JAN-2018") -> pd.DataFrame:
    try:
        return asyncio.run(fetch_la_refinery_data(start_date))
    except Exception as exc:
        logger.critical("Critical failure in LA_refinery: %s", exc)
        raise


__all__ = ["LA_refinery", "ScraperError", "fetch_la_refinery_data"]
