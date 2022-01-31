"""
Class for bumeran webpage control and data cleaning
"""
import re
import time
from datetime import timedelta, datetime
import unidecode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import project_constants as prc

class BumeranController:
    """Class for getting all raw data from multiple pages in Bumeran
    using Selenium"""
    #####################################
    ##Initialize instance of class
    def __init__(self, headless = True, max_pages = 10):
        self.headless = headless
        self.driver = None
        self.x_paths = {'num_jobs': "//h1[contains(@class, 'Title__H1')]/span",
                        'next_btn': "//*[contains(@class, 'Pagination__NextPage')]",
                        'review_btn' : "//button[contains(@class, 'openStateToggle')]",
                        #Card related
                        'cards': "//div[a[contains(@href, '/empleos/')]]",
                        'job': ".//h2[contains(@class, 'sc-keFjpB eGufqu')]/text()",
                        'company': ".//h3[contains(@class, 'sc-cpHetk kEXbuL')]/text()",
                        'location': ".//h3[contains(@class, 'sc-iuDHTM hxMtXj')]/text()",
                        'date': ".//h3[contains(@class, 'sc-AnqlK eJKbaZ')]/text()",
                        'link': ".//a/@href"
            }
        self.max_pages = max_pages
        self.banners_attended = False

    #####################################
    ##Get URL from keywords and limit date. Accessory functions too.
    @classmethod
    def format_keyword(cls, keywords):
        """Format keywords to use them in get_search_url() method"""
        clean_words = keywords.lower().strip()
        clean_words = unidecode.unidecode(clean_words)
        clean_words = re.sub(r'[^0-9a-zA-Z ]+', '', clean_words)
        clean_words = re.sub(' +', '-', clean_words)
        return clean_words

    @classmethod
    def format_date_limit(cls, date_limit):
        """Convert arbitrary date to one of the buckets in the
        get_date_limit_string() method"""
        date_array = [1, 3, 7, 15, 30]
        if date_limit > 30:
            return 30
        for num in date_array:
            if date_limit <= num:
                date = num
                break
        return date

    @classmethod
    def get_date_limit_string(cls, date_limit):
        """Get date limit string to use it in get_search_url() method"""
        string_base = "publicacion-"
        date_strings = {1: "ayer-",
                        3: "menor-a-3-dias-",
                        7: "menor-a-7-dias-",
                        15: "menor-a-15-dias-",
                        30: "menor-a-1-mes-"}
        return string_base + date_strings[cls.format_date_limit(date_limit)]

    @classmethod
    def get_search_url(cls, keywords, date_limit):
        """Get URL with search results"""
        url_base_1 = "https://www.bumeran.com.pe/empleos-"
        url_base_2 = "busqueda-"
        url_base_3 = ".html?recientes=true"
        url_l = url_base_1 + cls.get_date_limit_string(date_limit) + url_base_2
        url_r = cls.format_keyword(keywords) + url_base_3
        return url_l + url_r

    #####################################
    ##Open driver, load URL and attend banners
    def open_driver(self):
        """Open selenium chromedriver"""
        options = Options()
        options.headless = self.headless
        user_agent = prc.USER_AGENT
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-infobars')
        options.add_argument(f'user-agent={user_agent}')
        self.driver = webdriver.Chrome(prc.CHROMEDRIVER_PATH, options=options)

    def load_search_results(self, results_url):
        """Load webpage with the URL, wait for results and
        perform extra actions like attending banners if needed"""
        if not self.driver:
            self.open_driver()
        self.driver.get(results_url)
        num_results = self.get_number_results()
        print("Number of results for search: ", num_results)
        self.attend_banners()
        return num_results != 0

    def get_number_results(self):
        """Get the number of results of a search"""
        time.sleep(1)
        self.wait_for_element(self.x_paths['num_jobs'])
        result_string = self.driver.find_element_by_xpath(
            self.x_paths['num_jobs']).text
        result_string = result_string.replace(",", "")
        num_results = int(result_string.split('\n')[-1])
        return num_results

    def wait_for_element(self, x_path, wait_seconds = 10, clickable = False):
        """Wait for element defined by x_path"""
        try:
            if not clickable:
                WebDriverWait(self.driver, wait_seconds).until(
                    EC.presence_of_element_located((By.XPATH, x_path)))
            else:
                WebDriverWait(self.driver, wait_seconds).until(
                    EC.element_to_be_clickable((By.XPATH, x_path)))
        except TimeoutException:
            return False
        else:
            return True
    #####################################
    ##Return page data and loop through pages until max page number
    def get_page_data(self):
        """Get the raw data (page source) of a page of results"""
        page_source = None
        if self.wait_for_element(self.x_paths['next_btn']):
            page_source = self.driver.page_source
        return page_source

    def load_next_page(self):
        """Load next page if exists (Only loads it, this may not wait)."""
        button_list = self.driver.find_elements_by_xpath(self.x_paths['next_btn'])
        if button_list:
            button = button_list[0]
            if button.is_enabled():
                self.attend_banners()
                button.click()
                return True
        return False

    def get_all_pages(self, callback):
        """Get all pages from one loaded keyword search"""
        count = 1
        while count <= self.max_pages:
            print("Scraping page: ", count)
            yield callback(self.get_page_data())
            if self.load_next_page():
                count += 1
            else:
                break

    def attend_banners(self):
        """Attend banners. In this case, close the survey"""
        if not self.banners_attended:
            if self.wait_for_element(self.x_paths['review_btn'], 15, clickable=True):
                time.sleep(1)
                banner_btn = self.driver.find_element_by_xpath(self.x_paths['review_btn'])
                banner_btn.click()
                self.banners_attended = True

    #####################################
    ##Function that condenses all the control
    def scrape_bumeran(self, keyword, date_limit, callback):
        """Scrape a single keyword"""
        url = self.get_search_url(keyword, date_limit)
        page_data = None
        if self.load_search_results(url):
            self.update_xpaths()
            page_data = self.get_all_pages(callback)
        return page_data

    def multi_scrape_bumeran(self, keywords, date_limit, callback):
        """Scrape a list of keywords without closing the driver"""
        for keyword in keywords:
            yield self.scrape_bumeran(keyword, date_limit, callback)
        self.driver.close()
    
    #####################################
    ##Extra functions
    def update_xpaths(self):
        """Function that deals with varying xPaths for data"""
        #Card structure up to check date
        x_paths_tmp = {
            'job': "(./a/div/*)[1]//h2",
            'company': "(./a/div/*)[1]//h3",
            'location': "((./a/div/*)[2]//h3)[1]",
            'date': "((./a/div/*)[1]//h3)[3]"}
        #Update class values according to check date, fill tmpList with classes
        first_card = self.driver.find_element_by_xpath(self.x_paths['cards'])
        for key, value in x_paths_tmp.items():
            class_values = first_card.find_element_by_xpath(value).get_attribute('class')
            self.x_paths[key] = ".//*[contains(@class, '{}')]/text()".format(class_values)

class BumeranCleaner:
    """Class for bumeran data cleaning"""
    monthDict = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo':5 , 'junio':6, 'julio':7, 'agosto':8,
                'setiembre':9, 'septiembre':9, 'octubre':10,
                'noviembre':11, 'diciembre':12}

    base_URL = "https://www.bumeran.com.pe"

    @classmethod
    def clean_job(cls, string):
        """Method for cleaning job name"""
        tmpstring = re.sub(r'\(a\)', '', string.lower().strip())
        tmpstring = re.sub(r'[^0-9a-zA-Z \u00C0-\u00FF,]+', '', tmpstring)
        tmpstring = re.sub(r' +', ' ', tmpstring)
        return tmpstring

    @classmethod
    def clean_company(cls, string):
        """Method for cleaning company name"""
        return string.lower().strip()

    @classmethod
    def clean_location(cls, string):
        """Method for cleaning location data"""
        if string is None:
            return None
        return string.lower()

    @classmethod
    def get_lag_days(cls, split_string):
        """Auxiliary method for getting lag days"""
        len_string = len(split_string)
        lag_days = -1
        if len_string == 2:
            lag_days = (0 if split_string[1] == 'Hoy' else 1)
        elif len_string == 4:
            lag_days = int(split_string[2])
        return lag_days

    @classmethod
    def get_day_month_year(cls, split_string):
        """Auxiliary method for getting the date of a given format"""
        today = datetime.now().date()
        year = today.year
        month = cls.monthDict[split_string[4]]
        day = int(split_string[2])
        tmp = datetime(year, month, day)
        if today < tmp.date():
            tmp = datetime(tmp.year -1 , tmp.month, tmp.day)
        return tmp.date()

    @classmethod
    def clean_date(cls, string):
        """Method for cleaning date info"""
        today = datetime.now().date()
        tmp = re.split(' ', string)
        lag_days = cls.get_lag_days(tmp)
        return_date = None
        if lag_days >= 0:
            return_date = today - timedelta(days = lag_days)
        elif len(tmp) == 5:
            return_date = cls.get_day_month_year(tmp)
        return return_date

    @classmethod
    def clean_link(cls, string):
        """Method for cleaning link info"""
        return cls.base_URL + string

if __name__ == "__main__":
    #Constants
    KEYWORDS = ['Python', 'Practicante', 'Eléctrica']
    DATE_LIMIT = 15
    HEADLESS = True
    MAX_PAGES = 5
    #Obtain bumeran data
    bum_ctl = BumeranController(headless=HEADLESS, max_pages=MAX_PAGES)
    bum_ctl.multi_scrape_bumeran(KEYWORDS, DATE_LIMIT, print)
    