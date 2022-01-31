"""
Creates a crawler that uses selenium to get http responses, and process
them with scrapy
"""
import scrapy
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
#pylint: disable=import-error
from site_scraper.items import SiteScraperItem
from utils.web_control import select_website_control
#pylint: enable=import-error

class BasicSpider(scrapy.Spider):
    """Creates an spider that crawls the allowed websites"""
    name = 'basic'
    allowed_domains = ['web']

    def __init__(self, *args, **kwargs):
        """Initialize the scraper and extra arguments"""
        super().__init__(*args, **kwargs)
        self.ctl = None
        self.parameters = self.parameters

    def start_requests(self):
        """Makes a ficticious request to callback the parse method"""
        url = "https://es.wikipedia.org/wiki/Wikipedia:Portada"
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        """Parse each request defined by self.parameters"""
        self.ctl = select_website_control(self.parameters)
        generator_1 = self.ctl.multi_scrape_webpage(
                                            self.parameters.get('keywords'),
                                            self.parameters.get('date_lim'),
                                            self.process_page)
        for generator_2 in generator_1:
            for callback_generator in generator_2:
                for item in callback_generator:
                    yield item

    def process_page(self, text_output):
        """Auxiliary generator that processes an http response and
        gets all the required data from the page"""
        sel = Selector(text=text_output)
        x_paths = self.ctl.x_paths
        selectors = sel.xpath(x_paths['cards'])
        for selector in selectors:
            item = ItemLoader(item=SiteScraperItem(), selector=None)
            item.add_value('job', selector.xpath(x_paths['job']).extract())
            item.add_value('company', selector.xpath(x_paths['company']).extract())
            item.add_value('location', selector.xpath(x_paths['location']).extract())
            item.add_value('date', selector.xpath(x_paths['date']).extract())
            item.add_value('link', selector.xpath(x_paths['link']).extract())
            item.add_value('site', self.parameters.get('site'))
            item.add_value('opened', False)
            yield item.load_item()
    