import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "rakuten"
    allowed_domains = ["plaza.rakuten.co.jp"]
    start_urls = [
        "https://plaza.rakuten.co.jp/new/",
        "https://plaza.rakuten.co.jp/new/g300",
    ]

    link_extractor = LinkExtractor(
        allow_domains=["plaza.rakuten.co.jp"],
        allow=["/diary/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.BLOG},
            )
