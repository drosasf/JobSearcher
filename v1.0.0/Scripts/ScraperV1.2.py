# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 20:43:07 2022

*****************************
DATA FRAME COLUMNS: 
    ['Job', 'Company', 'Location', 'Date', 'Link']

*****************************
About classes:
    class DBHandling: this is a class only used for grouping functions
        related to database (csv) load and applying the second filter
        to a dataframe.
    class Scraper: this is an attempt to a general scraper class, grouping
        attributes and methods common to all scrapers to develop. Also, there
        is a lot of inheritance and overriding with the intention of improving
        code reusability.
    class BumeranScraper: child class of Scraper. There are lots of site-
        specific variables and procedures, so it's necessary to build a class
        for each scraper. Of course, the new code should be as small as
        possible, so it uses inheritance from the Scraper class.
    class TestBumeranScraper: child class of BumeranScraper. There are methods
        to test the search capabilities, loop exit conditions tests to verify
        if the scraper gathers only necessary data, tests for the primary and
        secondary filters, and tests to see if webpage opening capabilities
        are working as intended. Even if here doesn't look like I need
        inheritance, if for some reason I want to overload some method with
        an equivalent with more print functions, this could be useful.

*****************************
How to use:
    1 - Change parameters as desired. It's recommended to not update the database
    unless you need it since scraping takes some time.
    2 - Execute the code with the secondary parameters you desire. The first
    secondary search (strSearch1) is an AND search, meaning that all the words 
    inside the string must be in the job name. The second search (strSearch2)
    uses an OR logic, meaning that at least one of the words must be in the job
    name. If you don't want some of them, leave them with "".
    3 - The program will print the resulting dataframe. If you think that is too
    big, don't load the webpages and refine the search (more ANDs or less ORs).
    4 - Don't worry about testing because that is for developing purposes.
        
*****************************
Program description:
    Of course, the code needs better cleaning and formatting, but this is a
    first out of (at least) four (which come with more websites and features),
    so it will be a bit cumbersome to use the code. Anyways, here is an attempt:
    1 - Define the scraping and search parameters. The variable names are self-
    explanatory, but here are some guidelines about the less intuitive ones:
        - mainLimDays and secLimDays: primary and secondary date filter. They
        define how much days back from today are considered in the search.
        - mainSearch: primary search keywords which use the website database.
        Don't be too refined with this search since web posting jobs are bad
        with this.
        - secSearch1 and secSearch2: secondary search keywords. I have explained
        them in the "how to use", but a remainder is always good. secSearch1 uses
        AND logic, while secSearch2 uses OR logic. If you want to ignore one or
        both, use "" as name. In any case, it's recommended to use this for the
        finer searches since the databases are already loaded in pandas (and it
        is extremely fast).
    2 - Populate the database with data from the main search if the boolean of
    updateDatabase is True. The main search for names uses the Bumeran search
    capabilities which has some ugly problems. This is the reason for the second
    search.
    3 - Load the saved database and applies the second filter, asking if you want
    to open all links in chromium. This is useful because sometimes there are too
    much links, and if you open all you will take a lot of time to manually check
    them (and also to load). About the second filter, remember that the secSearch1
    acts using AND, and the secSearch2 acts using OR. The date filter overrides
    the first date filter.
    4 - There is some commented out code, this is for testing purposes. You can
    change some parameters in the class if you want to test with another parameters.

"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import timedelta, datetime
import re
import unidecode

class DBHandling:
    ##Dataframe load and saving
    def saveDF(df, csvName):
        df.to_csv(csvName, index=False)
        return

    def loadDF(csvName):
        return pd.read_csv(csvName)
    
    def loadAnd2ndFilterDF(csvName, secSearch1, secSearch2, secLimDays):
        dfTot = DBHandling.loadDF(csvName)
        dfTot['Date'] = pd.to_datetime(dfTot['Date']).dt.date
        return DBHandling.applySecFilters(dfTot, 
                            secSearch1, secSearch2, secLimDays)
    
    ##Secondary search related
    def arrayToSearch(string):
        tmpString = string.lower().strip()
        tmpString = re.sub(r' +', ' ', tmpString)
        return tmpString.split(" ")
    
    def applySecFilters(df, secSearch1, secSearch2, secLimDays):
        tmpDF = df
        #Apply first search criteria - "Must Have ALL"
        searchArray1 = DBHandling.arrayToSearch(secSearch1)
        for item in searchArray1:
            searchLogic = tmpDF['Job'].str.contains(item)
            tmpDF = tmpDF.loc[searchLogic]
        #Apply second search criteria - "Has at least ONE"
        searchArray2 = DBHandling.arrayToSearch(secSearch2)
        secondLogic = ~tmpDF['Job'].str.contains("")
        for item in searchArray2:
            tmpLogic = tmpDF['Job'].str.contains(item)
            secondLogic = secondLogic|tmpLogic
        tmpDF = tmpDF.loc[secondLogic]
        #Apply second date limit criteria
        dateLimit = datetime.now().date() - timedelta(days=secLimDays)
        tmpDF = tmpDF.loc[tmpDF['Date'] >= dateLimit]
        return tmpDF
        
class Scraper:
    ###############################
    ##Class constants
    defaults = {'headless': True,
                'userAgent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                              'AppleWebKit/537.36 (KHTML, like Gecko)',
                              ' Chrome/96.0.4664.110 Safari/537.36'),
                'maxPages': 9999,
                'limDays': 30}
    
    monthDict = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo':5 , 'junio':6, 'julio':7, 'agosto':8,
                'setiembre':9, 'septiembre':9, 'octubre':10,
                'noviembre':11, 'diciembre':12}
    
    ###############################
    ##Class initialization
    def __init__(self, headless = defaults['headless'],
                 userAgent = defaults['userAgent'],
                 maxPages = defaults['maxPages'],
                 limDays = defaults['limDays']):
        #Override
        self.xPaths = None
        #Class Arguments
        self.headless = headless
        self.userAgent = userAgent
        self.maxPages = maxPages
        self.limDays = limDays
        self.numPage = 0
        return
    
    ###############################
    ##Handling chromium
    def openDriver(self):
        #Set driver options, create and return it
        options = Options()
        options.headless = self.headless
        options.add_argument('--window-size=1920,1080')  
        options.add_argument('--disable-infobars')
        user_agent = self.userAgent
        options.add_argument(f'user-agent={user_agent}')
        CHROMEDRIVER_PATH = "C:\Program Files\chromedriver_win32\chromedriver.exe"
        self.driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options)
        return

    def closeDriver(self):
        self.driver.close()
        return

    def loadWebpage(self, url):
        self.driver.get(url)
        return
    
    ###############################
    ##Get URL from search string and load it
    #OVERRIDE FROM HERE
    def getSearchURL(self, strSearch):
        return "https://www.bumeran.com.pe/"
    
    #DONT OVERRIDE FROM HERE 
    def loadJobSearchResults(self, strSearch):
        #Get the URL of search results
        searchURL = self.getSearchURL(strSearch)
        #Create driver and load URL
        self.openDriver()
        self.loadWebpage(searchURL)
        #Wait for load, check if there are results and return the driver
        if self.jobFoundInSearch():
            self.waitForLoad()
            print("-The webpage should be loaded. Scraping...")
            return True
        else:
            print("-No search results for the job description")
            return False
    
    def waitForElement(self, elementPath, timeSeconds = 10):
        try:
            WebDriverWait(self.driver, timeSeconds).until(
                EC.element_to_be_clickable((By.XPATH, elementPath)))
        except:
            return False
        else:
            return True
    
    #OVERRIDE FROM HERE
    def waitForLoad(self):
        return
    
    def jobFoundInSearch(self):
        return True
    
    ###############################
    ##Get clean data from a page
    #Auxiliar Method - Common to all
    def getElementText(self, element, xPath):
        try:
            text = element.find_element_by_xpath(xPath).text
        except:
            text = None
        finally:
            return text
    
    #OVERRIDE THIS - Get data from a single card
    def getIndividualData(self, element):
        return [
            self.getElementText(element, self.xPaths['Job']),
            self.getElementText(element, self.xPaths['Company']),
            self.getElementText(element, self.xPaths['Location']),
            self.getElementText(element, self.xPaths['Date']),
            element.find_element_by_xpath(self.xPaths['Link']).get_attribute(
                'href'
            ),
        ]
    
    #DON'T OVERRIDE - Get data from a page
    def getPageData(self):
        #Locate all elements in the page
        try:
            cards = self.driver.find_elements_by_xpath(self.xPaths['cardElement'])
        except:
            return pd.DataFrame()
        data = [self.getIndividualData(element) for element in cards]
        #Convert the data to a dataframe, add column names and return
        dfPage = pd.DataFrame(data)
        if dfPage.empty:
            return dfPage
        columnNames = ['Job', 'Company', 'Location', 'Date', 'Link']
        dfPage.columns = columnNames
        return self.cleanDataFrame(dfPage)
    
    ###############################
    ##Clean dataframe
    #OVERRIDE THIS - Clean Method
    def cleanDataFrame(self, df):
        return df
    
    ###############################
    ##Page control and related
    #OVERRIDE THIS
    def getNumberPages(self):
        return 0
    
    #OVERRIDE THIS
    def nextButtonExists(self):
        return True
        
    #OVERRIDE THIS
    def nextPage(self):    
        return True
    
    #DON'T OVERRIDE
    def breakPageLoop(self, cmpDate):
        self.limDate = datetime.today().date() - timedelta(days = self.limDays)
        return self.numPage > self.maxPages or cmpDate < self.limDate
    
    ###############################
    ##Get data from all pages, save and load functions
    #DON'T OVERRIDE ANYTHING, COMMON TO ALL
    def getGlobalData(self):
        #Loop over the pages, getting their data until break conditions.
        dfArray = []
        try:
            print("Total pages: ", self.getNumberPages())
        except:
            print("Couldn't find number of pages. Maybe there are no results for the search.")
        self.numPage = 1
        while True:
            dfPage = self.getPageData()
            if dfPage.empty:
                break
            dfArray.append(dfPage)
            print("Page " + str(self.numPage) + " scraped.")
            self.numPage += 1
            if self.breakPageLoop(dfPage.loc[0, 'Date']):
                break
            elif self.nextPage():
                continue
            else:
                break

        #Join all data and return
        if not dfArray:
            print("Search didn't had any results.")
            return None
        return self.applyPrimaryFilter(pd.concat(dfArray, ignore_index = True))
    
    def applyPrimaryFilter(self, df):
        return df.loc[df['Date']>=self.limDate]
    
    def getDataFromSearch(self, strSearch):
        #Load driver with search results, get data and close driver
        self.loadJobSearchResults(strSearch)
        df = self.getGlobalData()
        self.closeDriver()
        return df
    
    def openLinksFromData(self, df):
        self.headless = False
        self.openDriver()
        for url in df['Link']:
            self.loadWebpage(url)
            self.driver.execute_script("window.open('');")
            WindowList = self.driver.window_handles
            self.driver.switch_to.window(WindowList[-1])
        return
    ###############################
    
class BumeranScraper(Scraper):
    ###############################
    ##Class initialization
    def __init__(self, headless = Scraper.defaults['headless'],
                 userAgent = Scraper.defaults['userAgent'],
                 maxPages =Scraper.defaults['maxPages'],
                 limDays = Scraper.defaults['limDays']):
        #Inherit initialization
        Scraper.__init__(self, headless, userAgent, maxPages, limDays)
        #Constants
        self.xPaths = {
            #NEXT BUTTON
            'nextButton': "//*[contains(@class, 'Pagination__NextPage')]",
            #CARD ELEMENTS
            'cardElement': "//div[contains(@class,'CardComponentWrapper')]",
            #DATA FROM CARD ELEMENTS
            'Job': ".//*[contains(@class,'mixins__Title')]",
            'Company': ".//*[contains(@class,'mixins__Company')]",
            'Location': ".//*[contains(@class,'mixins__DataInfo')]",
            'Date': ".//*[contains(@class,'mixins__CustomText')]",
            'Link': ".//*[contains(@href,'/empleos/')]",
            #HEADER FORNO JOB IS LOCATED
            'noJob': "//h3[contains(@class, 'sc-iBmynh')]",
            #ACTUAL PAGE
            'actPage': "//button[contains(@class, 'gZtPaa')]"
            }
        return
    
    ###############################
    ##Handling chromium: inherited
    
    ###############################
    ##Get URL from search string and load it
    #Overriding methods
    def getSearchURL(self, strSearch):
        #Base URLs
        baseURL1 = "https://www.bumeran.com.pe/empleos-busqueda-"
        baseURL2 = ".html?recientes=true"
        #Make it lowercase, clean some spaces and remove accents
        cleanWords = strSearch.lower().strip()
        cleanWords = unidecode.unidecode(cleanWords)
        cleanWords = unidecode.unidecode(cleanWords)
        #Strip non alphanumeric characters
        cleanWords = re.sub(r'[^0-9a-zA-Z ]+', '', cleanWords)
        #Replace multiple spaces with the string '-'
        cleanWords = re.sub(' +', '-', cleanWords)
        return baseURL1 + cleanWords + baseURL2
    
    def waitForLoad(self):
        self.waitForElement(self.xPaths['nextButton'])
        return
    
    def jobFoundInSearch(self):
        if self.waitForElement(self.xPaths['noJob'],3):
            message = self.driver.find_element_by_xpath(self.xPaths['noJob']).text
            return message != 'No encontramos lo que estás buscando'
        return True
    
    ###############################
    ##Get raw data from a page
    #Overriding methods
    def getIndividualData(self, element):
        return [
            self.getElementText(element, self.xPaths['Job']),
            self.getElementText(element, self.xPaths['Company']),
            self.getElementText(element, self.xPaths['Location']),
            self.getElementText(element, self.xPaths['Date']),
            element.find_element_by_xpath(self.xPaths['Link']).get_attribute(
                'href'
            ),
        ]    
    
    ###############################
    ##Clean dataframe
    #Overriding method
    def cleanDataFrame(self, df):
        #Remove non alphanumeric (keep commas), extra spaces,. Also lowercases it.
        df['Job'] = df['Job'].apply(self.cleanJobName)
        
        #To lowercase and strip extra spaces. Link is left as it, so it isn't here.
        df['Company'] = df['Company'].str.lower().str.strip()
        
        #Make location lowercase, erase job modality and split location
        df['Location'] = df['Location'].apply(self.cleanLocation)
            
        #Convert date to Day, Month and Year (as three columns replacing date)
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days = 1)
        df['Date'] = df['Date'].apply(self.getDate)
        return df
    
    #Auxiliary functions
    def cleanJobName(self, string):
        tmpString = re.sub(r'\(a\)', '', string.lower().strip())
        tmpString = re.sub(r'[^0-9a-zA-Z \u00C0-\u00FF,]+', '', tmpString)
        tmpString = re.sub(r' +', ' ', tmpString)
        return tmpString

    def cleanLocation(self, string):
        if string is None:
            return None
        tmpString = re.split('\n', string.lower())
        tmpString = tmpString[0]
        return tmpString
    
    def getDate(self, string):
        #Get Constants
        tmpString = re.split(' ', string)
        lenString = len(tmpString)
        #Obtain the date for all strings differentiating types by length
        if lenString == 2:
            return self.today if tmpString[1] == 'Hoy' else self.yesterday
        elif lenString == 4:
            return self.today - timedelta(days = int(tmpString[2]))
        elif lenString == 5:
            year = self.today.year
            tmpArray = [int(tmpString[2]), self.monthDict[tmpString[4]], year]
            tmpDate = datetime(tmpArray[2], tmpArray[1], tmpArray[0]).date()
            if self.today < tmpDate:
                tmpArray[2] = tmpArray[2] - 1
                tmpDate = datetime(tmpArray[2], tmpArray[1], tmpArray[0]).date()
            return tmpDate
        else:
            return None
        return string
    
    ###############################
    ##Page control and related
    #Overriding methods
    def getNumberPages(self):
        xPathBottom = "//div[contains(@class,'Pagination__PaginationComponent')]"
        tmpString = self.driver.find_element_by_xpath(xPathBottom).text
        return int(tmpString.split('\n')[-1])
    
    def nextButtonExists(self):
        return bool(self.driver.find_elements_by_xpath(self.xPaths['nextButton']))
        
    def nextPage(self):    
        if not self.nextButtonExists():
            return False
        button = self.driver.find_element_by_xpath(self.xPaths['nextButton'])
        if button.is_enabled():
            button.click()
            self.waitForElement(self.xPaths['nextButton'])
            return True
        else:
            return False
    
    ###############################
    ##Get data from all pages, save and load functions
    #From parent class, everything is inherited

class TestBumeranScraper(BumeranScraper):
    ##REMEMBER TO CHANGE THIS WHEN YOU CHANGE SOMETHING RELATED IN PARENT CLASSES
    ###############################
    ##Testing Searches
    def test_getSearchURL(self):
        print("Testing search function")
        searchList = ["Eléctrica", " Ingeniería ", "  Mantenimiento Eléctrico",
                      "Ingeniería  Eléctrica", "Proyectos", "Practicante Mantenimiento Proyectos"]
        for name in searchList:
            #Load driver with search results, get data and close driver
            print("Searching " + name)
            if self.loadJobSearchResults(name):
                print("Search OK: " + name)
            else:
                print("Search not found: " + name)
                self.driver.save_screenshot("t_getSearchURL " + name + ".png")
            self.closeDriver()
        return
    
    ###############################
    ##Test Exit Loop Conditions
    def test_exitLoop(self, strSearch = "Mantenimiento Eléctrico",
                      num = 5, limDays = 10):
        print("Testing exit loop conditions")
        self.loadJobSearchResults(strSearch)
        print("Total pages: ", self.getNumberPages())
        self.numPage = 1
        self.limDays = limDays
        self.maxPages = num
        def getScreenshot():
            try:
                actPageBtn = self.driver.find_element_by_xpath(self.xPaths['actPage'])
                print("Page:" + actPageBtn.text)
            except:
                print("Actual page not found")
            self.driver.save_screenshot("t_exitCondition.png")
            return
        
        while True:
            dfPage = self.getPageData()
            print("Page " + str(self.numPage) + " scraped.")
            if dfPage.empty:
                print("Empty")
                getScreenshot()
                break
            self.numPage = self.numPage + 1
            if self.breakPageLoop(dfPage.loc[0, 'Date']):
                print("Break condition")
                getScreenshot()
                break
            elif self.nextPage():
                continue
            else:
                print("No next page or unknown condition")
                getScreenshot()
                break
        return
        
    ###############################
    ##Test Primary Search
    def test_primarySearch(self):
        searchList = ["Eléctrica", "  Mantenimiento  Eléctrico",
                      "Practicante Mantenimiento Proyectos"]
        for item in searchList:
            self.loadJobSearchResults(item)
            df = self.getGlobalData()
            if df is None or df.empty:
                self.driver.save_screenshot("t_primarySearch " + item + ".png")
            else:
                print("Results for item: " + item)
                print(df)
            self.closeDriver()
        return
    
    ##Test Secondary Search
    def test_secondarySearch(self, refreshDB = False):
        secSearchList = ["Eléctrica", "  Mantenimiento  Eléctrico",
                      "Practicante Mantenimiento Proyectos"]
        csvName = "testSecSearch.csv"
        secSearch2 = ""
        secLimDays = 5
        if refreshDB:
            primarySearch = "Eléctrica"
            dfMain = self.getDataFromSearch(primarySearch)
            DBHandling.saveDF(dfMain, csvName)

        for secSearch1 in secSearchList:
            dfFiltered1 = DBHandling.loadAnd2ndFilterDF(csvName, secSearch1, secSearch2, secLimDays)
            dfFiltered2 = DBHandling.loadAnd2ndFilterDF(csvName, secSearch2, secSearch1, secLimDays)
            if dfFiltered1 is None or dfFiltered.empty:
                print("No results for AND filter: " + secSearch1)
            else:
                print("Printing AND search: " + secSearch1)
                print(dfFiltered1[['Job', 'Date']])

            if dfFiltered2 is None or dfFiltered.empty:
                print("No results for OR filter: " + secSearch1)
            else:
                print("Printing OR search: " + secSearch1)
                print(dfFiltered2[['Job', 'Date']])
        return
    
    ###############################
    ##Testing Open-On-Browser capabilities
    def test_openOnBrowser(self, refreshDB = False):
        secSearch1 = ""
        secSearch2 = "Mantenimiento Proyectos Profesional Eléctrico"
        csvName = "testOpenOnBrowser.csv"
        secLimDays = 10

        if refreshDB:
            primarySearch = "Eléctrica"
            dfMain = self.getDataFromSearch(primarySearch)
            DBHandling.saveDF(dfMain, csvName)
            if dfMain is None or dfMain.empty:
                print("No results for main search")
                return

        dfFiltered = DBHandling.loadAnd2ndFilterDF(csvName, secSearch1, secSearch2, secLimDays)
        if dfFiltered is None or dfFiltered.empty:
            print("No results for refined search")
            return

        if len(dfFiltered) > 5:
            dfFiltered = dfFiltered.head(5)
        print(dfFiltered)
        self.openLinksFromData(dfFiltered)
        return
        
if __name__  == "__main__":
    ###Scraping Parameters
    headless = True
    maxPages = 5
    
    ###Main Search Parameters
    updateDatabase = False
    csvName = "Search_Bumeran.csv"
    mainSearch = "Practicante"
    mainLimDays = 15
    
    ###Secondary Search Parameters
    openLinks = False
    secSearch1 = "Practicante"
    secSearch2 = "Eléctrica Mantenimiento Transmisión MT Proyectos Ingeniería Automatización Distribución"
    secLimDays = 5
    
    #Create scraper object
    bumeran = BumeranScraper(headless=headless, maxPages=maxPages, limDays=mainLimDays)
    
    #Print data and update on condition
    if updateDatabase:
        #Get new data
        df = bumeran.getDataFromSearch(mainSearch)
        #Overwrite CSV
        DBHandling.saveDF(df, csvName)
    
    #Load and apply second filter
    dfFiltered = DBHandling.loadAnd2ndFilterDF(csvName, secSearch1, secSearch2, secLimDays)
    print("Number of items: " + str(len(dfFiltered)))
    #print(dfFiltered)
    
    #Open webpages relevant to search
    openLinks = "N"
    openLinks = input("Open links? [Y/N]: ")
    if openLinks.lower() == "y":
        outputBrowser = Scraper()
        outputBrowser.openLinksFromData(dfFiltered)
    
    ####Automated Tests
    ##Search URL
    #bumeran.test_getSearchURL()
    #bumeran.test_exitLoop()
    #bumeran.test_primarySearch()
    #bumeran.test_secondarySearch()
    #bumeran.test_openOnBrowser()
