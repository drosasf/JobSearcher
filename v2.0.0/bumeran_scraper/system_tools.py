"""
This implements some general system tools that are required for cleanup
after the scrapers have closed.
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

CHROMEDRIVER_PATH = r"C:\Program Files\chromedriver_win32\chromedriver.exe"

def kill_all_chromedrivers():
    """Open a chromedriver to kill them all"""
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options)
    driver.quit()

if __name__ == "__main__":
    kill_all_chromedrivers()