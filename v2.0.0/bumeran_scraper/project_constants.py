"""
This file has all the constants for the scraper
"""
##Constants
CHROMEDRIVER_PATH = r"C:\Program Files\chromedriver_win32\chromedriver.exe"
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
              'AppleWebKit/537.36 (KHTML, like Gecko)',
              ' Chrome/96.0.4664.110 Safari/537.36')
##Program parameters
#Database parameters
DB_NAME = "testDB.db"
CSV_NAME = "items.csv"
SCRAPE_CSV = False
UPDATE_DB = False
SEARCH_DB = True
#Scrapy settings
FEED_FORMAT = 'csv'
FEED_URI = CSV_NAME
LOG_ENABLED = 'False'
EXTRA_CRAWLER_SETTINGS = {
        'USER_AGENT': 'Chrome/96.0.4664.110 Safari/537.36',
        'FEED_FORMAT': FEED_FORMAT,
        'FEED_URI': FEED_URI,
        'LOG_ENABLED': LOG_ENABLED}
#Scraping parameters
KWT_1 = ['Python', 'Practicante', 'Eléctrica']
KW2_2 = ['Python', 'Practicante', 'Eléctrica']
KEYWORDS = KWT_1
DATE_LIMIT = 15
HEADLESS = True
MAX_PAGES = 2
#Search parameters
MAX_PAST_DAYS = 1
KW_1 = ['eléctrico']
KEYWORDS_AND = [x.lower().strip() for x in KW_1]
KW_2 = ['data', 'ingeniería', 'mantenimiento']
KEYWORDS_OR = [x.lower().strip() for x in KW_2]
ONLY_NON_OPENED = True
