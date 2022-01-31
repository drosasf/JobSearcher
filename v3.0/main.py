"""
Main script for the project
"""
import os
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
#pylint: disable=import-error
import project_constants as prc
from utils.sql_control import DBControl
from site_scraper import settings as basic_settings
from site_scraper.spiders.basic import BasicSpider
#pylint: enable=import-error

def run_crawler_process(parameter_array):
    """Create and run a crawler with their settings and extra parameters"""
    crawler_settings = Settings()
    crawler_settings.setmodule(basic_settings)
    crawler_settings.setdict(prc.EXTRA_CRAWLER_SETTINGS)
    process = CrawlerProcess(settings = crawler_settings)
    for parameters in parameter_array:
        process.crawl(BasicSpider, parameters = parameters)
    process.start()

if __name__ == "__main__":
    #Program parameters
    OPTIONS = {'max_pages':prc.MAX_PAGES, 'headless':prc.HEADLESS}
    KEYWORDS = prc.KEYWORDS
    DATE_LIMIT = prc.DATE_LIMIT
    #Parameter object: keywords to search, site to search, date_limit for
    #the group of keywords, and options for webpage control
    #This should be obtained from the program
    PARAMETER_ARRAY = [{'keywords': KEYWORDS,
                       'site': x,
                       'date_lim': DATE_LIMIT,
                       'options': OPTIONS} for x in prc.ALLOWED_SITES]
    #Scrape and replace csv if parameter is true
    if prc.SCRAPE_CSV:
        #Delete csv if exists
        if os.path.exists(prc.CSV_NAME):
            os.remove(prc.CSV_NAME)
        #Create crawler and begin scraping
        run_crawler_process(PARAMETER_ARRAY)
    #Connect to DB if it will be used for something
    if prc.UPDATE_DB or prc.SEARCH_DB:
        #Create DB connection
        dbc = DBControl()
        dbc.connect_and_check_db(prc.DB_NAME, clear = False)
    #Update SQL database with CSV if parameter is true
    if prc.UPDATE_DB:
        #Update tables
        dbc.update_data_tbl(prc.CSV_NAME)
        dbc.update_search_tbl(dbc.generate_keyword_dict(prc.KEYWORDS))
    #Search in DB - Parameters and conversion
    if prc.SEARCH_DB:
        dbc.open_search_results()
    #Close DB connection if was opened
    if prc.UPDATE_DB or prc.SEARCH_DB:
        dbc.connection.close()
    print("Program done")
    