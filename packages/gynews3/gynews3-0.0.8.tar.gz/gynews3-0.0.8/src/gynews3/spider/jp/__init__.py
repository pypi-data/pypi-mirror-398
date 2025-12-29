from gynews3.spider import CommonSpider as BaseCommonSpider


class CommonSpider(BaseCommonSpider):
    custom_settings = {
        "GYNEWS3_SPIDER_PARSER": "jp_goose",
    }
