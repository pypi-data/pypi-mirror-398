import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "tsstv"
    allowed_domains = ["www.tss-tv.co.jp"]
    start_urls = ["https://www.tss-tv.co.jp/tssnews/"]

    link_extractor = LinkExtractor(
        allow_domains=["www.tss-tv.co.jp"],
        allow=["/tssnews/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.LOCAL_NEWS},
            )
