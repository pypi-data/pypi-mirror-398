import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tw import CommonSpider


class Spider(CommonSpider):
    name = "matters"
    allowed_domains = ["matters.town"]
    start_urls = ["https://matters.town/newest"]

    link_extractor = LinkExtractor(
        allow_domains=["matters.town"],
        allow=r"/a/",
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.BLOG},
            )
