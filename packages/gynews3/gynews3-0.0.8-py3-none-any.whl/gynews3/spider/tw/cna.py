import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tw import CommonSpider


class Spider(CommonSpider):
    name = "cna"
    allowed_domains = ["www.cna.com.tw"]
    start_urls = ["https://www.cna.com.tw/"]

    link_extractor = LinkExtractor(
        allow_domains=["www.cna.com.tw"],
        allow=r"/news/",
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
