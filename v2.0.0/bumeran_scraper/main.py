"""
Script that integrates scraping and database operations to complete the program.
"""
import os
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from bumeran_scraper.spiders.basic import BasicSpider
from bumeran_scraper import settings as basic_settings
from sql_control import DBControl
import project_constants as prc

def run_crawler():
    """Run crawler to fill csv with new data"""
    crawler_settings = Settings()
    crawler_settings.setmodule(basic_settings)
    crawler_settings.setdict(prc.EXTRA_CRAWLER_SETTINGS)
    process = CrawlerProcess(settings = crawler_settings)
    process.crawl(BasicSpider)
    process.start()

if __name__ == "__main__":
    #Scrape and replace csv if parameter is true
    if prc.SCRAPE_CSV:
        #Delete csv if exists
        if os.path.exists(prc.CSV_NAME):
            os.remove(prc.CSV_NAME)
        #Create crawler and begin scraping
        run_crawler()
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
    