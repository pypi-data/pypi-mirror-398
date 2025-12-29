import importlib
import pkgutil

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import signals

from gynews3.model import Link


def run_spider_and_get_results(spider_class, *args, **kwargs):
    scraped_items = []

    def item_scraped_handler(item, response, spider):
        scraped_items.append(dict(item))

    process = CrawlerProcess()

    crawler = process.create_crawler(spider_class, *args, **kwargs)
    crawler.signals.connect(item_scraped_handler, signal=signals.item_scraped)

    process.crawl(crawler)
    process.start()

    return [Link(**item) for item in scraped_items]


def load_spiders(category: str):
    spiders = []

    try:
        package_name = f"gynews3.spider.{category}"
        package = importlib.import_module(package_name)
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"gynews3.spider.{category}.{module_name}")
            try:
                spider = module.Spider
                if (
                    isinstance(spider, type)
                    and issubclass(spider, scrapy.Spider)
                    and spider is not scrapy.Spider
                ):
                    spiders.append(spider)
            except AttributeError:
                continue
    except ModuleNotFoundError:
        pass

    return spiders
