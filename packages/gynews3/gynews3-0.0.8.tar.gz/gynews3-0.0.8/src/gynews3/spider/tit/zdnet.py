import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tit import CommonSpider


class Spider(CommonSpider):
    name = "zdnet"
    allowed_domains = ["zdnet.com"]
    start_urls = ["https://www.zdnet.com/topic/developer/"]

    link_extractor = LinkExtractor(
        allow_domains=["zdnet.com"],
        allow=[r"/article/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.IT},
            )
