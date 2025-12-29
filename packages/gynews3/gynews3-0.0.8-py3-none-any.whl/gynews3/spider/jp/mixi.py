import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "mixi"
    allowed_domains = ["mixi.jp"]
    start_urls = ["https://mixi.jp/"]

    link_extractor = LinkExtractor(
        allow_domains=["mixi.jp"],
        allow=["/view_news.pl"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
