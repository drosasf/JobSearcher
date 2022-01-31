"""
General tools common to website control
"""
import re
import time
import unidecode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
#pylint: disable=import-error
import project_constants as prc
#pylint: enable=import-error

def select_website_control(param):
    """Return a control object based on the site to scrape"""
    allowed_sites = prc.ALLOWED_SITES
    ctl = None
    site = param.get('site')
    options = param.get('options')
    if site == allowed_sites[0]:
        ctl = BumeranControl(**options)
    elif site == allowed_sites[1]:
        ctl = ComputrabajoControl(**options)
    elif site == allowed_sites[2]:
        ctl = IndeedControl(**options)
    return ctl

class WebsiteControl:
    """
    Class containing some basic website control using selenium.
    """
    #####################################
    ##Initialize instance of class
    def __init__(self, **kwargs):
        #General arguments
        self.headless = kwargs.get('headless', True)
        self.driver = None
        self.extras_attended = False
        #Site specific arguments
        self.x_paths = None
        self.allowed_date_lims = None
        #Search specific arguments
        self.max_pages = kwargs.get('max_pages', 2)
        self.msg_print = ""

    #####################################
    ##Get URL from keywords and limit date
    def bucketize_date_limit(self, date_limit):
        """Bucketize date limit to the nearest upper allowed value"""
        max_lim = max(self.allowed_date_lims)
        limit =  max_lim
        for num in self.allowed_date_lims:
            if date_limit <= num:
                limit = num
                break
        return limit

    #Override following
    @classmethod
    def get_keyword_url_string(cls, keywords):
        """Get URL part from the keyword"""
        raise NotImplementedError()

    def get_date_limit_url_string(self, date_limit):
        """Get URL part from date limit"""
        raise NotImplementedError()

    def get_search_url(self, keywords, date_limit):
        """Get URL with search results"""
        raise NotImplementedError()

    #####################################
    ##Open driver, load URL and attend extras
    def open_driver(self):
        """Open selenium chromedriver"""
        options = Options()
        options.headless = self.headless
        user_agent = prc.USER_AGENT
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-infobars')
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(prc.CHROMEDRIVER_PATH,
                                       options=options)

    def wait_for_element(self, x_path, **kwargs):
        """Wait for element defined by x_path"""
        wait_seconds = kwargs.get("wait_seconds", 10)
        check_clickable = kwargs.get("check_clickable", False)
        try:
            if not check_clickable:
                WebDriverWait(self.driver, wait_seconds).until(
                    EC.presence_of_element_located((By.XPATH, x_path)))
            else:
                WebDriverWait(self.driver, wait_seconds).until(
                    EC.element_to_be_clickable((By.XPATH, x_path)))
        except TimeoutException:
            return False
        else:
            return True

    def load_search_results(self, results_url):
        """Load webpage with the URL, wait for results and
        attend extras if needed"""
        if not self.driver:
            self.open_driver()
        self.driver.get(results_url)
        num_results = self.get_number_results()
        print(self.msg_print + ": Number of results for search: ", num_results)
        self.attend_extras()
        return num_results != 0

    #Override following
    def get_number_results(self):
        """Get the number of results when a search is loaded"""
        raise NotImplementedError()

    def attend_extras(self):
        """Attend extras. In this case, close the survey"""
        raise NotImplementedError()

    #####################################
    ##Return page data and loop through pages until max page number
    def get_page_data(self):
        """Get the raw data (page source) from a page of results"""
        page_source = None
        if self.wait_for_page_load():
            page_source = self.driver.page_source
        return page_source

    def get_all_pages(self, function):
        """Get all pages from one loaded keyword search, yielding a
        page based generator"""
        count = 1
        while count <= self.max_pages:
            print(self.msg_print + ": Scraping page: ", count)
            yield function(self.get_page_data())
            if self.load_next_page():
                count += 1
            else:
                break

    #Override following
    def wait_for_page_load(self):
        """Wait for page load based on some condition"""
        raise NotImplementedError()

    def load_next_page(self):
        """Load next page if exists. Pd: This doesn't wait for load."""
        raise NotImplementedError()

    #####################################
    ##Methods that group all the control
    def scrape_webpage(self, keyword, date_limit, function):
        """Scrape a single keyword from one of the webpages"""
        url = self.get_search_url(keyword, date_limit)
        page_data = None
        if self.load_search_results(url):
            self.update_xpaths()
            page_data = self.get_all_pages(function)
        return page_data

    def multi_scrape_webpage(self, keywords, date_limit, function):
        """Scrape a list of keywords without closing the driver"""
        for keyword in keywords:
            yield self.scrape_webpage(keyword, date_limit, function)
        self.driver.close()

    #####################################
    ##Extra methods
    def unroll_generator(self, generator):
        """Function to unroll the results of the yielded generator
        in multi_scrape_webpage"""
        generator_kw = generator
        for generator_pg in generator_kw:
            for item in generator_pg:
                yield item

    def update_xpaths(self):
        """Function that deals with varying xPaths for scraped data"""
        raise NotImplementedError()

class BumeranControl(WebsiteControl):
    """Class for getting raw data from multiple pages in Bumeran
    using Selenium"""
    #####################################
    ##Initialize instance of class
    def __init__(self, **kwargs):
        #Initialize parent
        super().__init__(**kwargs)
        #Site specific arguments
        self.x_paths = {'num_jobs': "//h1[contains(@class, 'Title__H1')]/span",
                        'next_btn': "//*[contains(@class, 'Pagination__NextPage')]",
                        'review_btn' : "//button[contains(@class, 'openStateToggle')]",
                        #Card related
                        'cards': "//div[a[contains(@href, '/empleos/')]]",
                        'job': "",
                        'company': "",
                        'location': "",
                        'date': "",
                        'link': ".//a/@href"}
        self.allowed_date_lims = [1, 3, 7, 15, 30]
        self.msg_print = "Bumeran"

    #####################################
    ##Get URL from keywords and limit date
    @classmethod
    def get_keyword_url_string(cls, keywords):
        """Get URL part from the keyword"""
        clean_words = keywords.lower().strip()
        clean_words = unidecode.unidecode(clean_words)
        clean_words = re.sub(r'[^0-9a-zA-Z ]+', '', clean_words)
        clean_words = re.sub(' +', '-', clean_words)
        return clean_words

    def get_date_limit_url_string(self, date_limit):
        """Get URL part from date limit"""
        string_base = "publicacion-"
        date_strings = {1: "ayer-",
                        3: "menor-a-3-dias-",
                        7: "menor-a-7-dias-",
                        15: "menor-a-15-dias-",
                        30: "menor-a-1-mes-"}
        return string_base + date_strings[self.bucketize_date_limit(date_limit)]

    def get_search_url(self, keywords, date_limit):
        """Get URL with search results"""
        url_base_1 = "https://www.bumeran.com.pe/empleos-"
        url_base_2 = "busqueda-"
        url_base_3 = ".html?recientes=true"
        url_l = url_base_1 + self.get_date_limit_url_string(date_limit) + url_base_2
        url_r = self.get_keyword_url_string(keywords) + url_base_3
        return url_l + url_r

    #####################################
    ##Open driver, load URL and attend extras
    def get_number_results(self):
        """Get the number of results when a search is loaded"""
        time.sleep(1)
        self.wait_for_element(self.x_paths['num_jobs'])
        result_string = self.driver.find_element_by_xpath(
            self.x_paths['num_jobs']).text
        result_string = result_string.replace(",", "")
        num_results = int(result_string.split('\n')[-1])
        return num_results

    def attend_extras(self):
        """Attend extras. In this case, close the survey"""
        if not self.extras_attended:
            if self.wait_for_element(self.x_paths['review_btn'],
                                     wait_seconds=15,
                                     check_clickable=True):
                time.sleep(1)
                survey_btn = self.driver.find_element_by_xpath(
                    self.x_paths['review_btn'])
                survey_btn.click()
                self.extras_attended = True

    #####################################
    ##Return page data and loop through pages until max page number
    def wait_for_page_load(self):
        """Wait for page load based on some condition"""
        return self.wait_for_element(self.x_paths['next_btn'])

    def load_next_page(self):
        """Load next page if exists. Pd: This doesn't wait for load."""
        button_list = self.driver.find_elements_by_xpath(
            self.x_paths['next_btn'])
        if button_list:
            button = button_list[0]
            if button.is_enabled():
                button.click()
                return True
        return False

    #####################################
    ##Methods that group all the control

    #####################################
    ##Extra methods
    def update_xpaths(self):
        """Function that deals with varying xPaths for scraped data"""
        #Card structure up to check date
        x_paths_tmp = {
            'job': "(./a/div/*)[1]//h2",
            'company': "(./a/div/*)[1]//h3",
            'location': "((./a/div/*)[2]//h3)[1]",
            'date': "((./a/div/*)[1]//h3)[3]"}
        #Update xPaths with help of card structure
        cards = self.driver.find_elements_by_xpath(self.x_paths['cards'])
        for card in cards:
            try:
                for key, value in x_paths_tmp.items():
                    class_values = card.find_element_by_xpath(value).get_attribute('class')
                    self.x_paths[key] = ".//*[contains(@class, '{}')]/text()".format(class_values)
            except NoSuchElementException:
                continue
            else:
                break

class ComputrabajoControl(WebsiteControl):
    """Class for getting all raw data from multiple pages in Computrabajo
    using Selenium"""
    #####################################
    ##Initialize instance of class
    def __init__(self, **kwargs):
        #Initialize parent
        super().__init__(**kwargs)
        #Site specific arguments
        self.x_paths = {'num_jobs': "//div[contains(@class, 'title_page')]",
                        'next_btn': "//a[contains(@title, 'Siguiente')]",
                        'cookies_btn' :
                            "//a[contains(@aria-label,'dismiss cookie')]",
                        #Card related
                        'cards': "//article",
                        'job': "",
                        'company': "",
                        'location': "",
                        'date': "",
                        'link': ""}
        self.allowed_date_lims = [1, 3, 7, 15, 30]
        self.msg_print = "Computrabajo"

    #####################################
    ##Get URL from keywords and limit date
    @classmethod
    def get_keyword_url_string(cls, keywords):
        """Get URL part from the keyword"""
        clean_words = keywords.lower().strip()
        clean_words = unidecode.unidecode(clean_words)
        clean_words = re.sub(r'[^0-9a-zA-Z ]+', '', clean_words)
        clean_words = re.sub(' +', '-', clean_words)
        return clean_words

    def get_date_limit_url_string(self, date_limit):
        """Get URL part from date limit"""
        string_base = "?pubdate="
        return string_base + str(self.bucketize_date_limit(date_limit))

    def get_search_url(self, keywords, date_limit):
        """Get URL with search results"""
        url_1 = "https://www.computrabajo.com.pe/trabajo-de-"
        url_2 = self.get_keyword_url_string(keywords)
        url_3 = self.get_date_limit_url_string(date_limit)
        return url_1 + url_2 + url_3

    #####################################
    ##Open driver, load URL and attend extras
    def get_number_results(self):
        """Get the number of results when a search is loaded"""
        time.sleep(1)
        self.wait_for_element(self.x_paths['num_jobs'])
        result_string = self.driver.find_element_by_xpath(
            self.x_paths['num_jobs']).text
        result_string = result_string.replace(".", "")
        try:
            num_results = int(result_string.split()[0])
        except ValueError:
            num_results = 0
        return num_results

    def attend_extras(self):
        """Attend extras. In this case, accept cookies"""
        if not self.extras_attended:
            if self.wait_for_element(self.x_paths['cookies_btn']):
                time.sleep(1)
                cookies_btn = self.driver.find_element_by_xpath(
                    self.x_paths['cookies_btn'])
                cookies_btn.click()
                self.extras_attended = True

    #####################################
    ##Return page data and loop through pages until max page number
    def wait_for_page_load(self):
        """Wait for page load based on some condition"""
        return self.wait_for_element(self.x_paths['cards'])

    def load_next_page(self):
        """Load next page if exists. Pd: This doesn't wait for load."""
        button_list = self.driver.find_elements_by_xpath(
            self.x_paths['next_btn'])
        if button_list:
            button = button_list[0]
            if button.is_enabled():
                button.click()
                return True
        return False

    #####################################
    ##Methods that group all the control

    #####################################
    ##Extra methods
    def update_xpaths(self):
        """Function that deals with varying xPaths for scraped data"""
        #Card structure up to check date
        x_paths_tmp = {
            'job': ".//h1/a",
            'company': "//article/div/p[1]",
            'location': "//article/div/p[1]",
            'date': "//article/div/p[3]"}
        #Update xPaths with help of card structure
        cards = self.driver.find_elements_by_xpath(self.x_paths['cards'])
        for card in cards:
            try:
                for key, value in x_paths_tmp.items():
                    class_values = card.find_element_by_xpath(value).get_attribute('class')
                    self.x_paths[key] = ".//*[contains(@class, '{}')]/text()".format(class_values)
                    if key == 'company' or key == 'location':
                        self.x_paths[key] = ".//*[contains(@class, '{}')]//text()".format(class_values)
                    if key == 'job':
                        self.x_paths['link'] = ".//*[contains(@class, '{}')]/@href".format(class_values)
            except NoSuchElementException:
                continue
            else:
                break

class IndeedControl(WebsiteControl):
    """Class for getting all raw data from multiple pages in Indeed
    using Selenium"""
    #####################################
    ##Initialize instance of class
    def __init__(self, **kwargs):
        #Initialize parent
        super().__init__(**kwargs)
        #Site specific arguments
        self.x_paths = {'num_jobs': "//div[@id='searchCountPages']",
                        'next_btn': "//a[contains(@aria-label,'Siguiente')]",
                        'login_popup' : "//button[contains(@class,'icl-Card-close')\
                            and contains(@aria-label,'Close')]",
                        'email_popup' :
                            "//button[contains(@class,'popover')\
                                and contains(@aria-label,'Cerrar')]",
                        'group_btns': "//div[contains(@class,'pagination')]",
                        #Card related
                        'cards': "//a[contains(@class,'tapItem')]",
                        'job': ".//h2[contains(@class,'jobTitle')]/span/text()",
                        'company': ".//span[contains(@class,'companyName')]//text()",
                        'location': ".//div[contains(@class,'companyLocation')]/text()",
                        'date': ".//span[contains(@class,'date')]/text()",
                        'link': "./@href"}
        self.allowed_date_lims = [1, 3, 7, 14]
        self.msg_print = "Indeed"

    #####################################
    ##Get URL from keywords and limit date
    @classmethod
    def get_keyword_url_string(cls, keywords):
        """Get URL part from the keyword"""
        clean_words = keywords.lower().strip()
        clean_words = re.sub(' +', '+', clean_words)
        return clean_words

    def get_date_limit_url_string(self, date_limit):
        """Get URL part from date limit"""
        string_base = "&fromage="
        return string_base + str(self.bucketize_date_limit(date_limit))

    def get_search_url(self, keywords, date_limit):
        """Get URL with search results"""
        url_1 = "https://pe.indeed.com/jobs?q="
        url_2 = "&sort=date"
        url_k = self.get_keyword_url_string(keywords)
        url_d = self.get_date_limit_url_string(date_limit)
        return url_1 + url_k + url_d + url_2

    #####################################
    ##Open driver, load URL and attend extras
    def get_number_results(self):
        """Get the number of results when a search is loaded"""
        time.sleep(1)
        self.wait_for_element(self.x_paths['num_jobs'])
        result = self.driver.find_elements_by_xpath(self.x_paths['num_jobs'])
        #result_string = result_string.replace(".", "")
        num_results = 0
        try:
            if result:
                num_results = int(result[0].text.split()[-2].replace(",",""))
        except ValueError:
            num_results = 0
        return num_results

    def attend_extras(self):
        """Attend extras. In this case, close a screen that blocks all"""
        button_list = self.driver.find_elements_by_xpath(
            self.x_paths['login_popup'])
        if button_list:
            element = button_list[0]
            if element.is_displayed() and element.is_enabled():
                element.click()
                time.sleep(1)
        button_list = self.driver.find_elements_by_xpath(
            self.x_paths['email_popup'])
        if button_list:
            element = button_list[0]
            self.wait_for_element_display(self.x_paths['email_popup'])
            if element.is_displayed():
                element.click()
                time.sleep(1)
                self.driver.refresh()

    def wait_for_element_display(self, x_path, **kwargs):
        """Wait for element defined by x_path - Display"""
        wait_seconds = kwargs.get("wait_seconds", 10)
        try:
            WebDriverWait(self.driver, wait_seconds).until(
                EC.visibility_of_element_located((By.XPATH, x_path)))
        except TimeoutException:
            return False
        else:
            return True

    #####################################
    ##Return page data and loop through pages until max page number
    def wait_for_page_load(self):
        """Wait for page load based on some condition"""
        return self.wait_for_element(self.x_paths['cards'])

    def load_next_page(self):
        """Load next page if exists. Pd: This doesn't wait for load."""
        self.attend_extras()
        button_list = self.driver.find_elements_by_xpath(
            self.x_paths['next_btn'])
        if button_list:
            button = button_list[0]
            if button.is_enabled():
                button.click()
                return True
        return False

    #####################################
    ##Methods that group all the control

    #####################################
    ##Extra methods
    def update_xpaths(self):
        """Function that deals with varying xPaths for scraped data"""
        #self.x_paths = self.x_paths
        None
    