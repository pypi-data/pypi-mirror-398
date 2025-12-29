import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "ats"
    allowed_domains = ["www.at-s.com"]
    start_urls = ["https://www.at-s.com/snews/"]

    custom_settings = {
        "GYNEWS3_SPIDER_PARSER": "jp_goose",
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
        },
    }

    link_extractor = LinkExtractor(
        allow_domains=["www.at-s.com"],
        allow=["/article/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.LOCAL_NEWS},
            )
