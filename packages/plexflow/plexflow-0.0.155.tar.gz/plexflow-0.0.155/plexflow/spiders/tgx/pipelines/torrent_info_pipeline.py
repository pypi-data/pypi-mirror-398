from plexflow.utils.torrent.extract.tgx import extract_torrent_info

class TorrentInfoPipeline:
    def process_item(self, item, spider):
        meta = item.get("meta", {})
        response = item.get("response", None)

        info = extract_torrent_info(html_content=response.text)

        meta = {**meta, **info}
        item["meta"] = meta
        return item
