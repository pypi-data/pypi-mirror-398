import scrapy
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "note"
    allowed_domains = ["note.com"]
    start_urls = ["https://note.com/notemagazine/m/mf2e92ffd6658"]

    link_extractor = LinkExtractor(
        allow_domains=["note.com"],
        allow=r"/n/",
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_article,
                cb_kwargs={"linkType": LinkType.BLOG},
            )
