import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tw import CommonSpider


class Spider(CommonSpider):
    name = "apple"
    allowed_domains = ["news.nextapple.com"]
    start_urls = ["https://news.nextapple.com/realtime/latest"]

    link_extractor = LinkExtractor(
        allow_domains=["news.nextapple.com"],
        allow=[r"/politics/", r"/local/", r"/life/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
