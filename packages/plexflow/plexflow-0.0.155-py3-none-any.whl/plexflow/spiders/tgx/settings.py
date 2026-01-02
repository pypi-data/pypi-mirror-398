# User-agent settings
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

# Obey robots.txt rules (set to False during development)
ROBOTSTXT_OBEY = False

# Configure pipelines (enable or disable as needed)
ITEM_PIPELINES = {
    "plexflow.spiders.tgx.pipelines.validation_pipeline.ValidationPipeline": 100,
    "plexflow.spiders.tgx.pipelines.torrent_info_pipeline.TorrentInfoPipeline": 600,
    "plexflow.spiders.tgx.pipelines.meta_pipeline.MetaPipeline": 800,
    "plexflow.spiders.tgx.pipelines.publish_pipeline.PublishPipeline": 900,
}

# Configure logging
LOG_ENABLED = True
LOG_LEVEL = "INFO"
LOG_FORMATTER = "plexflow.spiders.quiet_logger.QuietLogFormatter"
# LOG_FILE = "scrapy.log"

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Configure concurrent requests
CONCURRENT_REQUESTS = 10
CONCURRENT_REQUESTS_PER_DOMAIN = 10

# Extend default headers (optional)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en",
}

DOWNLOAD_TIMEOUT = 15