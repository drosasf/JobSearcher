"""
DATA CLEANING HAPPENS HERE
Define your item pipelines here

Don't forget to add your pipeline to the ITEM_PIPELINES setting
See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

useful for handling different item types with a single interface
"""
from itemadapter import ItemAdapter
from bumeran_control import BumeranCleaner as bcl

class BumeranScraperPipeline:
    """Class for processing incoming data"""
    @classmethod
    def process_bumeran_adapter(cls, adapter):
        """Cleaning incoming data from parsing bumeran"""
        adapter['job'] = bcl.clean_job(adapter['job'][0])
        adapter['company'] = bcl.clean_company(adapter['company'][0])
        adapter['location'] = bcl.clean_location(adapter['location'][0])
        adapter['date'] = bcl.clean_date(adapter['date'][0])
        adapter['link'] = bcl.clean_link(adapter['link'][0])
        adapter['opened'] = adapter['opened'][0]
        return adapter

    @classmethod
    def process_item(cls, item, spider):
        """Cleaning incoming data"""
        _ = spider
        adapter = ItemAdapter(item)
        adapter = cls.process_bumeran_adapter(adapter)
        return item
    