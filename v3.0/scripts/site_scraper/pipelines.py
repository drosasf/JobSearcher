"""
DATA CLEANING HAPPENS HERE
Define your item pipelines here

Don't forget to add your pipeline to the ITEM_PIPELINES setting
See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
"""
from itemadapter import ItemAdapter
#pylint: disable=import-error
from utils.data_cleaner import select_data_cleaner
#pylint: enable=import-error

class SiteScraperPipeline:
    """Class for cleaning incoming data"""
    @classmethod
    def process_item(cls, item, spider):
        """Cleaning incoming data"""
        _ = spider
        adapter = ItemAdapter(item)
        try:
            adapter = cls.clean_adapter(adapter)
        except:
            None
        return item

    @classmethod
    def clean_adapter(cls, adapter):
        """Cleaning incoming data from parsing bumeran"""
        adapter['opened'] = adapter['opened'][0]
        adapter['site'] = adapter['site'][0]
        cleaner = select_data_cleaner(adapter['site'])
        adapter['job'] = cleaner.clean_job(adapter['job'])
        adapter['company'] = cleaner.clean_company(adapter['company'])
        adapter['location'] = cleaner.clean_location(adapter['location'])
        adapter['date'] = cleaner.clean_date(adapter['date'])
        adapter['link'] = cleaner.clean_link(adapter['link'])
        return adapter
    