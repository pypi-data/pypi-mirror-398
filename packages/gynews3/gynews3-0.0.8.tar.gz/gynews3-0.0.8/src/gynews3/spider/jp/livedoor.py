import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "livedoor"
    start_urls = [
        "https://blog.livedoor.com/category/84/recent",
        "https://blog.livedoor.com/category/1/recent",
    ]

    link_extractor = LinkExtractor(
        allow=["/archives/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.BLOG},
            )
