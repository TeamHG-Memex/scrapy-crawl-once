# -*- coding: utf-8 -*-
import time

from sqlitedict import SqliteDict

from scrapy.utils.request import request_fingerprint


class CrawlOnceDB:
    """ DB for requests deduplication.

    A key is a request fingerprint or ``request.meta['crawl_once_key']``
    (if defined).

    Value is a timestamp by default, or ``request.meta['crawl_once_value']``
    (if defined).
    """
    def __init__(self, path):
        self.db = SqliteDict(
            filename=path,
            tablename='requests',
            autocommit=True,
        )
        self.path = path

    def mark_seen(self, request):
        key = self._get_key(request)
        self.db[key] = request.meta.get('crawl_once_value', time.time())

    def is_seen(self, request):
        key = self._get_key(request)
        return key in self.db

    def unsee(self, request):
        key = self._get_key(request)
        try:
            del self.db[key]
        except KeyError:
            pass

    def _get_key(self, request):
        return (request.meta.get('crawl_once_key') or
                request_fingerprint(request))

    def close(self):
        self.db.close()

    def __len__(self):
        return len(self.db)
