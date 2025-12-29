import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tec import CommonSpider


class Spider(CommonSpider):
    name = "electronicsweekly"
    allowed_domains = ["electronicsweekly.com"]
    start_urls = ["https://www.electronicsweekly.com/news/"]

    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        },
    }

    link_extractor = LinkExtractor(
        allow_domains=["electronicsweekly.com"],
        allow=[r"/news/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.ELECTRONICS},
            )
