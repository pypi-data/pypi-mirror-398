import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tit import CommonSpider


class Spider(CommonSpider):
    name = "arstechnica"
    allowed_domains = ["arstechnica.com"]
    start_urls = ["https://arstechnica.com/ai/", "https://arstechnica.com/gadgets/"]

    link_extractor = LinkExtractor(
        allow_domains=["arstechnica.com"],
        allow=[r"/gadgets/", r"/ai/"],
        deny=[r"/gadgets/$", r"/ai/$"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.IT},
            )
