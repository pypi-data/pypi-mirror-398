import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tit import CommonSpider


class Spider(CommonSpider):
    name = "codezine"
    allowed_domains = ["codezine.jp"]
    start_urls = ["https://codezine.jp/news"]

    link_extractor = LinkExtractor(
        allow_domains=["codezine.jp"],
        allow=[r"/news/detail/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.IT},
            )
