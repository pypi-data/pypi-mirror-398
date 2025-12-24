"""
Web Screenshot Module - Visual Capture of Web Services
Uses Selenium for headless browser screenshots
"""

import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class WebScreenshot:
    """Captures screenshots of web services"""
    
    def __init__(self, browser='chrome', headless=True, output_dir='reports/screenshots'):
        """
        Initialize screenshot capturer
        
        Args:
            browser: Browser to use ('chrome' or 'firefox')
            headless: Run in headless mode
            output_dir: Directory to save screenshots
        """
        self.browser = browser
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.driver = None
        self._initialized = False
    
    def _init_driver(self):
        """Initialize browser driver (lazy loading)"""
        if self._initialized:
            return
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.firefox import GeckoDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.firefox.service import Service as FirefoxService
            
            if self.browser == 'chrome':
                options = ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            
            elif self.browser == 'firefox':
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument('--headless')
                
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=options)
            
            self._initialized = True
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize browser: {e}")
    
    def capture(self, url: str, filename: str = None, timeout: int = 10) -> Optional[str]:
        """
        Capture screenshot of URL
        
        Args:
            url: Target URL
            filename: Output filename (auto-generated if None)
            timeout: Page load timeout in seconds
        
        Returns:
            Path to screenshot file or None if failed
        """
        try:
            self._init_driver()
            
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            # Generate filename if not provided
            if not filename:
                domain = url.split('//')[1].split('/')[0].replace(':', '_')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{domain}_{timestamp}.png"
            
            output_path = self.output_dir / filename
            
            # Navigate and capture
            self.driver.set_page_load_timeout(timeout)
            self.driver.get(url)
            self.driver.save_screenshot(str(output_path))
            
            # Create thumbnail
            self._create_thumbnail(output_path)
            
            return str(output_path)
            
        except Exception as e:
            print(f"Screenshot failed for {url}: {e}")
            return None
    
    def capture_multiple(self, urls: List[str], timeout: int = 10) -> List[str]:
        """
        Capture screenshots of multiple URLs
        
        Args:
            urls: List of URLs
            timeout: Page load timeout
        
        Returns:
            List of screenshot paths
        """
        screenshots = []
        for url in urls:
            screenshot = self.capture(url, timeout=timeout)
            if screenshot:
                screenshots.append(screenshot)
        return screenshots
    
    def _create_thumbnail(self, image_path: Path, size: tuple = (300, 300)):
        """Create thumbnail version of screenshot"""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            img.thumbnail(size)
            
            thumb_path = image_path.parent / f"{image_path.stem}_thumb{image_path.suffix}"
            img.save(thumb_path)
            
        except:
            # PIL not installed or thumbnail failed, skip
            pass
    
    def close(self):
        """Close browser driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self._initialized = False
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Quick test
if __name__ == "__main__":
    print("Testing Web Screenshot...")
    print("Note: Requires selenium and webdriver-manager")
    print("Install with: pip install selenium webdriver-manager")
    
    try:
        screenshotter = WebScreenshot()
        
        url = "https://example.com"
        print(f"\nCapturing screenshot of: {url}")
        
        result = screenshotter.capture(url)
        
        if result:
            print(f"Screenshot saved: {result}")
        else:
            print("Screenshot failed")
        
        screenshotter.close()
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to install dependencies:")
        print("pip install selenium webdriver-manager Pillow")
