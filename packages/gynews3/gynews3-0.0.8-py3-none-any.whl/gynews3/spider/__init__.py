import scrapy
import trafilatura

from functools import cached_property
from gynews3.model import Link, LinkType
from gynews3.content import create_jp_goose, extract_content


class CommonSpider(scrapy.Spider):
    @cached_property
    def g(self):
        return create_jp_goose()

    def _parse_article_jp_goose(self, response, linkType: LinkType):
        article = extract_content(self.g, response.text)

        if not article.cleaned_text:
            self.logger.warning(f"No content extracted from {response.url}")
            return

        yield Link(
            type=linkType,
            url=response.url,
            title=article.title,
            content=article.cleaned_text,
        )

    def _parse_article_trafilatura(self, response, linkType: LinkType):
        content = trafilatura.extract(response.text)
        if not content:
            self.logger.warning(f"No content extracted from {response.url}")
            return

        metadata = trafilatura.extract_metadata(response.text)

        yield Link(
            type=linkType,
            url=response.url,
            title=metadata.title,
            content=content,
        )

    def parse_article(self, response, linkType: LinkType):
        if self.settings.get("GYNEWS3_SPIDER_PARSER") == "jp_goose":
            yield from self._parse_article_jp_goose(response, linkType)
        else:
            yield from self._parse_article_trafilatura(response, linkType)
