"""
Creates a crawler that uses selenium to get http responses, and process
them with scrapy
"""
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from bumeran_control import BumeranController
from bumeran_scraper.items import BumeranScraperItem
import project_constants as prc

class BasicSpider(scrapy.Spider):
    """Creates the spider class to scrape the webpage"""
    name = 'basic'
    allowed_domains = ['web']

    def __init__(self, *args, **kwargs):
        """Initialize the scraper and extra arguments"""
        super().__init__(*args, **kwargs)
        self.bum_ctl = None

    def start_requests(self):
        """Makes a ficticious request to callback the parse method"""
        url = "https://es.wikipedia.org/wiki/Wikipedia:Portada"
        yield scrapy.Request(url=url, callback=self.parse)

    def process_page(self, text_output):
        """Auxiliary generator that processes an http response and
        gets all the required data from the page"""
        sel = Selector(text=text_output)
        x_paths = self.bum_ctl.x_paths
        selectors = sel.xpath(x_paths['cards'])
        for selector in selectors:
            item = ItemLoader(item=BumeranScraperItem(), selector=None)
            item.add_value('job', selector.xpath(x_paths['job']).extract())
            item.add_value('company', selector.xpath(x_paths['company']).extract())
            item.add_value('location', selector.xpath(x_paths['location']).extract())
            item.add_value('date', selector.xpath(x_paths['date']).extract())
            item.add_value('link', selector.xpath(x_paths['link']).extract())
            item.add_value('site', "Bumeran")
            item.add_value('opened', False)
            yield item.load_item()

    def parse(self, response, **kwargs):
        """Get the data for different keywords using selenium and scrapy"""
        #Constants
        keywords = prc.KEYWORDS
        date_limit = prc.DATE_LIMIT
        headless = prc.HEADLESS
        max_pages = prc.MAX_PAGES
        #Obtain bumeran data
        self.bum_ctl = BumeranController(headless=headless, max_pages=max_pages)
        generator_1 = self.bum_ctl.multi_scrape_bumeran(keywords, date_limit, self.process_page)
        for generator_2 in generator_1:
            for callback_generator in generator_2:
                for item in callback_generator:
                    yield item

    def spider_closed(self, spider):
        """Close drivers when spider finishes scraping"""
        _ = spider
        self.bum_ctl.driver.close()
    