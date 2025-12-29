import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "tbs"
    allowed_domains = ["newsdig.tbs.co.jp"]
    start_urls = ["https://newsdig.tbs.co.jp/list/latest"]

    link_extractor = LinkExtractor(
        allow_domains=["newsdig.tbs.co.jp"],
        allow=["/articles/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
