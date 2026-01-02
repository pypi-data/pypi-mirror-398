import scrapy
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider
from scrapy import signals
from plexflow.utils.thread_safe.safe_set import ThreadSafeSet
from plexflow.utils.thread_safe.safe_list import ThreadSafeList
import logging

class TgxSpider(scrapy.Spider): 
    name = "tgx_spider"
    session_expired: bool = False
    
    def __init__(self, pages, host='https://torrentgalaxy.to', cookies: dict = None, callback=None):
        self.pages = set(pages)
        self.host = host
        self.cookies = cookies or {}
        
        self.original_batch = ThreadSafeSet.from_set(self.pages)
        self.finished_batch = ThreadSafeList()
        self.callback = callback

    @property
    def finished_ids(self):
        return set(map(lambda x: x.get("id"), self.finished_batch))
    
    @property
    def finished_items(self):
        return self.finished_batch.to_list()
    
    @property
    def original_ids(self):
        return self.original_batch.to_set()
    
    @property
    def unfinished_ids(self):
        return self.original_batch.difference(self.finished_ids).to_set()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TgxSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    
    def mark_page_as_finished(self, meta):
        self.finished_batch.append(meta)
    
    def start_requests(self):
        for page_id in self.pages:
            yield scrapy.Request(
                f'{self.host}/torrent/{page_id}', 
                self.parse, 
                meta={'id': page_id},
                cookies=self.cookies)
    
    def parse(self, response):
        if self.session_expired:
            raise CloseSpider("Session Expired")
        soup = BeautifulSoup(response.text, 'html.parser')
        page_number = response.meta["id"]
        
        return {"soup": soup, "valid": True, "response": response, "meta": {"id": page_number}}

    def spider_closed(self, spider):
        # Code to run when the spider is closed
        logging.info(f"Spider {spider.name} closing. Finished scraping {len(self.finished_ids)} pages.")

        logging.info(f"{len(self.unfinished_ids)} pages were not scraped.")

        logging.info("Spider closed.")
        
        if self.callback:
            self.callback(self)