import scrapy
import trafilatura
from scrapy.linkextractors import LinkExtractor


from gynews3.model import Link, LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "chiebukuro"
    allowed_domains = ["chiebukuro.yahoo.co.jp"]
    start_urls = ["https://chiebukuro.yahoo.co.jp/question/list?flg=1&fr=common-navi"]

    link_extractor = LinkExtractor(
        allow_domains=["chiebukuro.yahoo.co.jp"],
        allow=["/question_detail/"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse_article)

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
