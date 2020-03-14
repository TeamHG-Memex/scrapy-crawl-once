# -*- coding: utf-8 -*-
import os
import logging

from scrapy import signals
from scrapy.utils.project import data_path
from scrapy.exceptions import IgnoreRequest, NotConfigured

from .db import CrawlOnceDB

logger = logging.getLogger(__name__)


class CrawlOnceMiddleware(object):
    """
    This spider and downloader middleware allows to avoid re-crawling pages 
    which were already downloaded in previous crawls.
    
    To enable it, modify your settings.py::
    
        SPIDER_MIDDLEWARES = {
            # ...
            'scrapy_crawl_once.CrawlOnceMiddleware': 100,
            # ...            
        }
        
        DOWNLOADER_MIDDLEWARES = {
            # ...
            'scrapy_crawl_once.CrawlOnceMiddleware': 50,            
            # ...
        }
    
    By default it does nothing. To avoid crawling a particular page 
    multiple times set ``request.meta['crawl_once'] = True``. Other 
    ``request.meta`` keys:
     
    * ``crawl_once_value`` - a value to store in DB. By default, timestamp
      is stored.
    * ``crawl_once_key`` - request unique id; by default request_fingerprint
      is used.
    
    Settings:
    
    * ``CRAWL_ONCE_ENABLED`` - set it to False to disable middleware. 
      Default is True.
    * ``CRAWL_ONCE_PATH`` - a path to a folder with crawled requests database.
      By default ``.scrapy/crawl_once/`` path is used; this folder contains 
      ``<spider_name>.sqlite`` files with databases of seen requests.
    * ``CRAWL_ONCE_DEFAULT`` - default value for ``crawl_once`` meta key
      (False by default). When True, all requests are handled by 
      this middleware unless disabled explicitly using 
      ``request.meta['crawl_once'] = False``.

    This middleware puts all requests to the Scheduler, and then filters
    them out at Downloader.
    """

    def __init__(self, path, stats, default):
        self.path = path
        self.stats = stats
        self.default = default

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        if not s.getbool('CRAWL_ONCE_ENABLED', True):
            raise NotConfigured()
        path = data_path(s.get('CRAWL_ONCE_PATH', 'crawl_once'),
                         createdir=True)
        default = s.getbool('CRAWL_ONCE_DEFAULT', default=False)
        o = cls(path, crawler.stats, default)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_opened(self, spider):
        self.db = self._create_db(spider)
        num_records = len(self.db)
        logger.info("Opened crawl database %r with %d existing records" % (
            self.db.path, num_records
        ))
        self.stats.set_value('crawl_once/initial', num_records)

    def spider_closed(self, spider):
        self.db.close()

    def _create_db(self, spider):
        path = os.path.join(self.path, '%s.sqlite' % spider.name)
        return CrawlOnceDB(path)

    # spider middleware interface
    def process_spider_output(self, response, result, spider):
        for r in result:
            yield r

        # response is crawled, store its fingerprint in DB if crawl_once
        # is requested.
        if response.meta.get('crawl_once', self.default):
            self.db.mark_seen(request=response.request)
            self.stats.inc_value('crawl_once/stored')

    # downloader middleware interface
    def process_request(self, request, spider):
        if not request.meta.get('crawl_once', self.default):
            return
        if self.db.is_seen(request):
            self.stats.inc_value('crawl_once/ignored')
            raise IgnoreRequest()
