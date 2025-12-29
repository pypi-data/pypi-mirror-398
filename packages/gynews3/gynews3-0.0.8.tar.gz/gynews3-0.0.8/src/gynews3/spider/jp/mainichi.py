import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "mainichi"
    allowed_domains = ["mainichi.jp"]
    start_urls = ["https://mainichi.jp"]

    link_extractor = LinkExtractor(
        allow_domains=["mainichi.jp"],
        restrict_css=".maintab-content-wrapper a",
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
