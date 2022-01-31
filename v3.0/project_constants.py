"""
Constants and parameters for the project
"""
##################################
#Search parameters
MAX_PAST_DAYS = 15
KW_1 = ['practica', 'práctica', 'profesional', 'trainee', 
        'graduado']
KEYWORDS_AND = [x.lower().strip() for x in KW_1]
KW_A = ['instrum', 'mantenimiento', 'mina', 'operaci', 
        'electric', 'eléctric', 'electrónic', 'electronic',
        'proyect', 'automatizac', 'energ', ' miner']
KW_B = []
KW_2 = KW_A
KEYWORDS_OR = [x.lower().strip() for x in KW_2]
ONLY_NON_OPENED = True
##################################
#Program parameters
#Scraping parameters
KWM_TEST = ['Mina']
KWM_NORMAL = ['Eléctrica', 'Eléctrico', 'Electricista', 'Practicante',
              'Mina', 'Trainee', 'Python', 'Mantenimiento', 'Proyecto']
KEYWORDS = KWM_NORMAL
DATE_LIMIT = 1
HEADLESS = True
MAX_PAGES = 50
#Database parameters
DB_NAME = "testDB.db"
CSV_NAME = "items.csv"
BOOLEANS_0 = (True, True, True)
BOOLEANS_1 = (True, True, False)
BOOLEANS_2 = (False, False, True)
SCRAPE_CSV, UPDATE_DB, SEARCH_DB = BOOLEANS_0
##################################
#Program constants and settings
CHROMEDRIVER_PATH = r"C:\Program Files\chromedriver_win32\chromedriver.exe"
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
              'AppleWebKit/537.36 (KHTML, like Gecko)',
              ' Chrome/96.0.4664.110 Safari/537.36')
ALLOWED_SITES = ['Bumeran', 'Computrabajo', 'Indeed']
#Scrapy settings
FEED_FORMAT = 'csv'
FEED_URI = CSV_NAME
LOG_ENABLED = 'False'
EXTRA_CRAWLER_SETTINGS = {
        'USER_AGENT': 'Chrome/96.0.4664.110 Safari/537.36',
        'FEED_FORMAT': FEED_FORMAT,
        'FEED_URI': FEED_URI,
        'LOG_ENABLED': LOG_ENABLED}
