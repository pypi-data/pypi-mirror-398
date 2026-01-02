from datetime import datetime

class MetaPipeline:
    def process_item(self, item, spider):
        response = item.get("response", None)
        meta = item.get("meta", {})

        deleted = "it has probably been deleted" in response.text
        date_last_scrape = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        meta = {**meta, "deleted": deleted, "date_last_scrape": date_last_scrape}
        item["meta"] = meta
        return item
