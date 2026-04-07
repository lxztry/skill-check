#!/usr/bin/env python3
"""
Browser - Example web automation script
"""

import os
import time
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Element:
    """Represents a DOM element"""
    tag: str
    text: str
    attrs: Dict[str, str]
    selector: str


class Browser:
    """Example browser automation wrapper"""
    
    def __init__(self, browser: str = None, headless: bool = True):
        self.browser_name = browser or os.environ.get('BROWSER', 'chrome').lower()
        self.headless = headless if headless is not None else os.environ.get('HEADLESS', 'true').lower() == 'true'
        self.implicit_wait = int(os.environ.get('IMPLICIT_WAIT', '10'))
        self._driver = None
        self._initialize()
    
    def _initialize(self):
        """Initialize browser driver"""
        if self.browser_name == 'chrome':
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                self._driver = webdriver.Chrome(options=options)
                self._driver.implicitly_wait(self.implicit_wait)
                logger.info("Chrome browser initialized")
            except ImportError:
                logger.error("Selenium not installed. Run: pip install selenium")
                raise
        elif self.browser_name == 'firefox':
            try:
                from selenium import webdriver
                from selenium.webdriver.firefox.options import Options
                
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                
                self._driver = webdriver.Firefox(options=options)
                self._driver.implicitly_wait(self.implicit_wait)
                logger.info("Firefox browser initialized")
            except ImportError:
                logger.error("Selenium not installed. Run: pip install selenium")
                raise
        else:
            raise ValueError(f"Unsupported browser: {self.browser_name}")
    
    def navigate(self, url: str) -> None:
        """Navigate to URL"""
        logger.info(f"Navigating to {url}")
        self._driver.get(url)
    
    def get_title(self) -> str:
        """Get page title"""
        return self._driver.title
    
    def get_url(self) -> str:
        """Get current URL"""
        return self._driver.current_url
    
    def screenshot(self, path: str) -> None:
        """Save screenshot"""
        self._driver.save_screenshot(path)
        logger.info(f"Screenshot saved to {path}")
    
    def find_element(self, selector: str) -> Optional[Element]:
        """Find element by CSS selector"""
        from selenium.webdriver.common.by import By
        try:
            el = self._driver.find_element(By.CSS_SELECTOR, selector)
            return Element(
                tag=el.tag_name,
                text=el.text,
                attrs=dict(el.get_attribute('class')),
                selector=selector
            )
        except Exception as e:
            logger.warning(f"Element not found: {selector} - {e}")
            return None
    
    def find_elements(self, selector: str) -> List[Element]:
        """Find all elements by CSS selector"""
        from selenium.webdriver.common.by import By
        elements = []
        try:
            els = self._driver.find_elements(By.CSS_SELECTOR, selector)
            for el in els:
                elements.append(Element(
                    tag=el.tag_name,
                    text=el.text,
                    attrs=dict(el.get_attribute('class')),
                    selector=selector
                ))
        except Exception as e:
            logger.warning(f"Elements not found: {selector} - {e}")
        return elements
    
    def fill_form(self, data: Dict[str, str]) -> None:
        """Fill form fields"""
        from selenium.webdriver.common.by import By
        for selector, value in data.items():
            try:
                el = self._driver.find_element(By.CSS_SELECTOR, selector)
                el.clear()
                el.send_keys(value)
                logger.info(f"Filled {selector}")
            except Exception as e:
                logger.warning(f"Could not fill {selector}: {e}")
    
    def click(self, selector: str) -> None:
        """Click element"""
        from selenium.webdriver.common.by import By
        el = self._driver.find_element(By.CSS_SELECTOR, selector)
        el.click()
    
    def wait_for(self, selector: str, timeout: int = 10) -> bool:
        """Wait for element to appear"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        try:
            WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        """Close browser"""
        if self._driver:
            self._driver.quit()
            logger.info("Browser closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Browser automation')
    parser.add_argument('--url', required=True, help='URL to navigate to')
    parser.add_argument('--screenshot', help='Save screenshot to file')
    parser.add_argument('--headless', type=bool, default=True, help='Run headless')
    
    args = parser.parse_args()
    
    with Browser(headless=args.headless) as browser:
        browser.navigate(args.url)
        print(f"Title: {browser.get_title()}")
        print(f"URL: {browser.get_url()}")
        
        if args.screenshot:
            browser.screenshot(args.screenshot)
