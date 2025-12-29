import goose3


def create_goose() -> goose3.Goose:
    return goose3.Goose()


def create_jp_goose() -> goose3.Goose:
    from goose3.text import StopWordsJapanese

    return goose3.Goose({"stopwords_class": StopWordsJapanese})


def extract_content_from_url(g: goose3.Goose, url: str) -> goose3.Article:
    # TODO: handle http proxy
    article = g.extract(url=url)
    return article


def extract_content(g: goose3.Goose, html: str) -> goose3.Article:
    article = g.extract(raw_html=html)
    return article
