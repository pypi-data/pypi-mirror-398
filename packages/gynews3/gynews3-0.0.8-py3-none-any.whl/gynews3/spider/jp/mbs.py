import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "mbs"
    allowed_domains = ["www.mbs.jp"]
    start_urls = ["https://www.mbs.jp/news/kansainews/"]

    link_extractor = LinkExtractor(
        allow_domains=["www.mbs.jp"],
        allow=["/news/kansainews/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.LOCAL_NEWS},
            )
