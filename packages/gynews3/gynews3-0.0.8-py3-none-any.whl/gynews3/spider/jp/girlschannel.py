import scrapy
import trafilatura
from scrapy.linkextractors import LinkExtractor

from gynews3.model import LinkType, Link
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "girlschannel"
    allowed_domains = ["girlschannel.net"]
    start_urls = ["https://girlschannel.net/new/"]

    link_extractor = LinkExtractor(
        allow_domains=["girlschannel.net"],
        allow=["/topics/"],
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
            type=LinkType.QA,
            url=response.url,
            title=metadata.title,
            content=content,
        )
