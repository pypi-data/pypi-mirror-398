import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tit import CommonSpider


class Spider(CommonSpider):
    name = "infoworld"
    allowed_domains = ["infoworld.com"]
    start_urls = ["https://www.infoworld.com/"]

    link_extractor = LinkExtractor(
        allow_domains=["infoworld.com"],
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
