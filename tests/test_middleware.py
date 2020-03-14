# -*- coding: utf-8 -*-
import os
from contextlib import contextmanager

import pytest
import scrapy
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.http.response import Response
from scrapy.utils.test import get_crawler

from scrapy_crawl_once import CrawlOnceMiddleware


@contextmanager
def opened_middleware(crawler):
    mw = CrawlOnceMiddleware.from_crawler(crawler)
    crawler.spider = crawler._create_spider('example')
    mw.spider_opened(crawler.spider)
    try:
        yield mw
    finally:
        mw.spider_closed(crawler.spider)


def test_configured():
    crawler = get_crawler()
    mw = CrawlOnceMiddleware.from_crawler(crawler)
    assert mw.path is not None


def test_not_configured():
    crawler = get_crawler(settings_dict={'CRAWL_ONCE_ENABLED': False})
    with pytest.raises(NotConfigured):
        CrawlOnceMiddleware.from_crawler(crawler)


def test_db_created(tmpdir):
    crawler = get_crawler(settings_dict={
        'CRAWL_ONCE_PATH': str(tmpdir)
    })
    with opened_middleware(crawler) as mw:
        assert os.path.isfile(mw.db.filename)
        assert mw.db.filename.startswith(str(tmpdir))
    assert os.path.isfile(mw.db.filename)


def test_crawl(tmpdir):
    settings = {'CRAWL_ONCE_PATH': str(tmpdir)}
    crawler = get_crawler(settings_dict=settings)
    req1 = scrapy.Request('http://example.com/1', meta={'crawl_once': True})
    req2 = scrapy.Request('http://example.com/2')
    req3 = scrapy.Request('http://example.com/3', meta={'crawl_once': True})

    resp1 = Response(req1.url, request=req1)
    resp2 = Response(req2.url, request=req2)

    with opened_middleware(crawler) as mw:

        # 1. check spider middleware interface
        assert len(mw.db) == 0
        assert crawler.stats.get_value('crawl_once/initial') == 0
        output = [{}, scrapy.Request('http://example.com')]

        # crawl_once is False
        res = list(mw.process_spider_output(resp2, output, crawler.spider))
        assert res == output
        assert len(mw.db) == 0

        # crawl_once is True
        res = list(mw.process_spider_output(resp1, output, crawler.spider))
        assert res == output
        assert len(mw.db) == 1
        assert crawler.stats.get_value('crawl_once/initial') == 0
        assert crawler.stats.get_value('crawl_once/stored') == 1

        # 2. check downloader middleware interface
        assert mw.process_request(req2, crawler.spider) is None
        assert crawler.stats.get_value('crawl_once/ignored', 0) == 0

        with pytest.raises(IgnoreRequest):
            mw.process_request(req1, crawler.spider)
        assert crawler.stats.get_value('crawl_once/ignored', 0) == 1

        assert mw.process_request(req3, crawler.spider) is None
        assert crawler.stats.get_value('crawl_once/ignored', 0) == 1
        assert crawler.stats.get_value('crawl_once/initial') == 0

    crawler = get_crawler(settings_dict=settings)
    with opened_middleware(crawler) as mw2:
        # it reuses the same file, so there are records
        assert len(mw2.db) == 1
        assert crawler.stats.get_value('crawl_once/initial') == 1
        assert mw2.process_request(req2, crawler.spider) is None
        assert crawler.stats.get_value('crawl_once/ignored', 0) == 0
        with pytest.raises(IgnoreRequest):
            mw2.process_request(req1, crawler.spider)
        assert crawler.stats.get_value('crawl_once/ignored', 0) == 1
        assert mw2.process_request(req3, crawler.spider) is None
