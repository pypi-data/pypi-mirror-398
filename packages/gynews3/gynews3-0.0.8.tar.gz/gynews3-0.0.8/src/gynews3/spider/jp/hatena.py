import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "hatena"
    allowed_domains = ["hatena.blog", "hatenablog.com"]
    start_urls = ["https://hatena.blog/"]

    link_extractor = LinkExtractor(
        allow_domains=["hatenablog.com"],
        allow=r"/entry/",
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.BLOG},
            )
