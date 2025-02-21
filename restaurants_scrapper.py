# Description: This script is used to scrap the restaurants data from the website
import csv
from time import sleep
from __future__ import annotations
import logging

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext, PlaywrightError, Locator

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RestaurantScraper:
    """
    This class is used to scrap the restaurants data from the website
    """
    def __init__(self, region: str = "DownTown Toronto", output_file: str = "restaurants.csv") -> None:
        """
        Constructor
        """
        self.region: str = region
        self.output_file: str = output_file
        self.browser: Browser|None = None
        self.page: Page|None = None
        self.context: BrowserContext|None = None
        self.restaurants: list[dict] = []
        logger.info("RestrauntScrapper object created")

    def initialize_browser(self) -> None:
        """
        This method is used to initialize the browser
        """
        try:
            self.browser = sync_playwright().start().chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            logger.info("Browser initialized")

            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            )
            logger.info("Browser context created")

            self.page = self.context.new_page()
            logger.info("Page created")
            
            logger.info("Browser, context and page initialized")

        except PlaywrightError as e:
            logger.error(f"Playwright error during initialization: {e}")
            self._cleanup_resources()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}")
            self._cleanup_resources()
            raise
    
    def _cleanup_resources(self) -> None:
        """
        This method is used to cleanup the resources
        """
        try:
            if self.page:
                self.page.close()
                logger.info("Page closed")
            if self.context:
                self.context.close()
                logger.info("Context closed")
            if self.browser:
                self.browser.close()
                logger.info("Browser closed")
        except PlaywrightError as e:
            logger.error(f"Playwright error during cleanup: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {e}")
            raise

    def accept_cookies(self) -> None:
        """
        This method is used to accept the cookies
        """
        try:
            accept_all_button: Locator = self.page.get_by_role("button", name="Accept all", exact=True)
            if accept_all_button.is_visible():
                accept_all_button.click()
                logger.info("Accept All button clicked")
                self.page.wait_for_load_state("networkidle")
            else:
                logger.info("Accept All button not found or is not visible")
        except PlaywrightError as e:
            logger.debug("Cookie consent check timed out (likely not present)")
        except Exception as e:
            logger.warning(f"Unexpected error during accepting cookies: {e}")

    def get_restaurants(self) -> None:
        """
        This method is used to scrap the restaurants 
        """
        try:
            url: str = f"https://www.google.com/search?q=restaurants+in+{self.region}"
            self.page.goto(url, wait_until="domcontentloaded")
            logger.info(f"Page navigated to: {url}")
            
            self.page.wait_for_selector("div.g", state="attached", timeout=10000)
            self.accept_cookies()
            
            res: Locator = self.page.locator("div.g")
            logger.info(f"Found {res.count()} restaurants")

            for r in range(res.count()):
                try:
                    restaurant: Locator = res.nth(r)
                    details: dict = self._get_restaurant_details(restaurant)
                    if details : self.restaurants.append(details)
                    logger.info(f"Restaurant {r+1} scrapped")
                except Exception as e:
                    logger.error(f"Error during scrapping restaurant {r+1}: {e}")
                    continue

            logger.info("Restaurants scrapped")

        except PlaywrightError as e:
            logger.error(f"Playwright error during scrapping restaurants: {e}")
            self._cleanup_resources()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scrapping restaurants: {e}")
            self._cleanup_resources()
            raise

    def _get_restaurant_details(self, restaurant: Locator) -> dict:
        """
        This method is used to get the details of the restaurant
        """
        try:
            html: str = restaurant.inner_html()
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")

            name: str = self._safe_extract(soup, "h3", "N/A")
            rating: str = self._safe_extract(soup, "span[aria-label]", "N/A")
            address: str = self._safe_extract(soup, "span.LrzXr", "N/A")
            phone: str = self._safe_extract(soup, "span[data-dtype='d3ifr']", "N/A")

            return {
                "Name": name,
                "Rating": rating,
                "Address": address,
                "Phone": phone
            }
        except PlaywrightError as e:
            logger.error(f"Playwright error during getting restaurant details: {e}")
            self._cleanup_resources()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during getting restaurant details: {e}")
            self._cleanup_resources()
            raise

    def _safe_extract(self, soup: BeautifulSoup, selector: str, default: str) -> str:
        """
        This method is used to extract the data from the soup object
        """
        try:
            return soup.select_one(selector).get_text(strip=True) if soup.select_one(selector) else default
        except Exception as e:
            logger.error(f"Error during extracting data: {e}")
            return "N/A"
