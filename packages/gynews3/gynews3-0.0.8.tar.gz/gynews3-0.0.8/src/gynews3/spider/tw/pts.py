import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.tw import CommonSpider


class Spider(CommonSpider):
    name = "pts"
    allowed_domains = ["news.pts.org.tw"]
    start_urls = ["https://news.pts.org.tw/dailynews"]

    link_extractor = LinkExtractor(
        allow_domains=["news.pts.org.tw"],
        allow=r"/article/",
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.NEWS},
            )
