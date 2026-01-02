# Import necessary modules
import json
from pathlib import Path
import logging

class PublishPipeline:
    def process_item(self, item, spider):
        meta = item.get("meta", {})
        if meta is None:
            logging.info("Meta is None. Skipping...")  
            return item
        
        spider.mark_page_as_finished(meta)
        return item
