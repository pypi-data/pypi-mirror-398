import scrapy

class QuietLogFormatter(scrapy.logformatter.LogFormatter):
    def scraped(self, item, response, spider):
        return (
            super().scraped(item, response, spider)
            if spider.settings.getbool("LOG_SCRAPED_ITEMS")
            else None
        )
