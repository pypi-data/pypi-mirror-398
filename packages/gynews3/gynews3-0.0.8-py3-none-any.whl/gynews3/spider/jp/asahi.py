import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "asahi"
    allowed_domains = ["asahi.com"]
    start_urls = ["https://www.asahi.com"]

    link_extractor = LinkExtractor(
        allow_domains=["asahi.com"],
        restrict_css=".p-topNews",
        allow=["/articles/"],
        deny_domains=["digital.asahi.com"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
