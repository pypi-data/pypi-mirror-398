import scrapy
from scrapy.linkextractors import LinkExtractor
from unstructured.partition.html import partition_html
from unstructured.documents.elements import NarrativeText

from gynews3.model import Link, LinkType
from gynews3.spider.jp import CommonSpider


class Spider(CommonSpider):
    name = "shikoku"
    allowed_domains = ["www.shikoku-np.co.jp"]
    start_urls = ["https://www.shikoku-np.co.jp/"]

    link_extractor = LinkExtractor(
        allow_domains=["www.shikoku-np.co.jp"],
        allow=["/national/"],
        deny=[".aspx"],
        unique=True,
    )

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                link.url,
                callback=self.parse_article,
            )

    def parse_article(self, response):
        main_text = self.extract_main_text(response.text)
        if not main_text:
            self.logger.warning(f"No content extracted from {response.url}")
            return
        title = response.css("title::text").get()
        yield Link(
            type=LinkType.LOCAL_NEWS,
            url=response.url,
            title=title,
            content=main_text,
        )

    def extract_main_text(self, html_content):
        elements = partition_html(text=html_content)

        body_elements = []

        for element in elements:
            text = str(element).strip()
            if len(text) > 100:
                body_elements.append(text)

        return "\n\n".join(body_elements)
