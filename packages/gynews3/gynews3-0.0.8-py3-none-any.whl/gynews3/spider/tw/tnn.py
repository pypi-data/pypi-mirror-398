import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tw import CommonSpider


class Spider(CommonSpider):
    name = "tnn"
    allowed_domains = ["news.tnn.tw"]
    start_urls = [
        "https://tc.news.tnn.tw/index.html",
        "https://ml.news.tnn.tw/index.html",
    ]

    link_extractor = LinkExtractor(
        allow_domains=["news.tnn.tw"],
        allow=r"/news.html",
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
