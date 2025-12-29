import scrapy
import trafilatura
from scrapy.linkextractors import LinkExtractor

from gynews3.model import Link, LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "5ch"
    allowed_domains = ["5ch.net"]
    start_urls = ["https://headline.5ch.net/bbynews/"]

    link_extractor = LinkExtractor(
        allow_domains=["5ch.net"],
        allow=["/read.cgi/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
            )

    def parse_article(self, response):
        content = trafilatura.extract(response.text)
        if not content:
            self.logger.warning(f"No content extracted from {response.url}")
            return

        metadata = trafilatura.extract_metadata(response.text)

        yield Link(
            type=LinkType.BOARD,
            url=response.url,
            title=metadata.title,
            content=content,
        )
