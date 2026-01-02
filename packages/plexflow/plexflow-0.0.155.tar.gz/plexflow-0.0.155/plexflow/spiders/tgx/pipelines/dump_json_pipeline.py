# Import necessary modules
import json
from pathlib import Path

class DumpJsonPipeline:
    def __init__(self):
        self.data = []

    def process_item(self, item, spider):
        # Process each item and add it to the data list
        self.data.append(dict(item.get("meta", {})))
        return item

    def close_spider(self, spider):
        target_path = Path(spider.dump_folder)
        tag = spider.tag
        if isinstance(tag, bytes):
            tag = tag.decode("utf-8")

        print("type of tag:", type(tag))
        print("tag:", tag)

        json_file_path = target_path / f"{tag}.json"

        # Create the directory if it doesn't exist
        target_path.mkdir(exist_ok=True)

        # Write the data to the JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)
