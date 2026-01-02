
class ValidationPipeline:
    def process_item(self, item, spider):
        response = item.get("response", None)
        meta = item.get("meta", {})
        
        if "it has probably been deleted" not in response.text and "magnet:?xt" not in response.text:
            print(f"Invalid HTML for number {meta.get('id')}")
            meta["valid"] = False
            spider.session_expired = True
        else:
            meta["valid"] = True        
        
        meta["errored"] = False

        item["meta"] = meta
        return item
