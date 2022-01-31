"""
Created on Tue Jan 18 15:26:31 2022

Refactoring V1.2
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
    
    def getLagDays(self, splitString):
        lenString = len(splitString)
        
        #Obtain the date for all strings differentiating types by length
        if lenString == 2:
            return 0 if splitString[1] == 'Hoy' else 1
        elif lenString == 4:
            return int(splitString[2])
        else:
            return -1
    
    def getLagOneYear(self, splitString):
        year = self.today.year
        month = self.monthDict[splitString[4]]
        day = int(splitString[2])
        tmp = datetime(year, month, day).date()
        if self.today < tmp:
            tmp = datetime(tmp.year -1 , tmp.month, tmp.day)
        return tmp.date()
    
    def getDate(self, string):
        #Get Constants
        if not hasattr(self, "today"):
            self.today = datetime.now().date()
        
        tmp = re.split(' ', string)
        lagDays = self.getLagDays(tmp)
        
        #Obtain the date for all strings differentiating types by length
        if lagDays >= 0:
            return self.today - timedelta(days = lagDays)
        elif len(tmp) == 5:
            return self.getLagOneYear(tmp)
        else:
            return None
    
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
    def getScreenshot(self):
        try:
            actPageBtn = self.driver.find_element_by_xpath(self.xPaths['actPage'])
            print("Page:" + actPageBtn.text)
        except:
            print("Actual page not found")
        self.driver.save_screenshot("t_exitCondition.png")
        return
    
    def test_exitLoop(self, strSearch = "Mantenimiento Eléctrico",
                      num = 5, limDays = 10):
        print("Testing exit loop conditions")
        self.loadJobSearchResults(strSearch)
        print("Total pages: ", self.getNumberPages())
        self.numPage = 1
        self.limDays = limDays
        self.maxPages = num
        
        while True:
            dfPage = self.getPageData()
            print("Page " + str(self.numPage) + " scraped.")
            if dfPage.empty:
                print("Empty")
                self.getScreenshot()
                break
            
            self.numPage += 1
            if self.breakPageLoop(dfPage.loc[0, 'Date']):
                print("Break condition")
                self.getScreenshot()
                break
            elif self.nextPage():
                continue
            else:
                print("No next page or unknown condition")
                self.getScreenshot()
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
            if dfFiltered1 is None or dfFiltered1.empty:
                print("No results for AND filter: " + secSearch1)
            else:
                print("Printing AND search: " + secSearch1)
                print(dfFiltered1[['Job', 'Date']])

            if dfFiltered2 is None or dfFiltered2.empty:
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
    
    items = ["Publicado Hoy", "Publicado Ayer", "Publicado hace 3 días",
             "Publicado hace 4 días", "Publicado el 28 de noviembre", "Publicado el 19 de enero"]
    for k in items:
        print(bumeran.getDate(k))
    """
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
"""