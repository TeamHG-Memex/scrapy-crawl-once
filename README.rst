scrapy-crawl-once
=================

.. image:: https://img.shields.io/pypi/v/scrapy-crawl-once.svg
   :target: https://pypi.python.org/pypi/scrapy-crawl-once
   :alt: PyPI Version

.. image:: https://travis-ci.org/TeamHG-Memex/scrapy-crawl-once.svg?branch=master
   :target: http://travis-ci.org/TeamHG-Memex/scrapy-crawl-once
   :alt: Build Status

.. image:: http://codecov.io/github/TeamHG-Memex/scrapy-crawl-once/coverage.svg?branch=master
   :target: http://codecov.io/github/TeamHG-Memex/scrapy-crawl-once?branch=master
   :alt: Code Coverage

This package provides a Scrapy_ middleware which allows to avoid re-crawling
pages which were already downloaded in previous crawls.

.. _Scrapy: https://scrapy.org/

License is MIT.

Installation
------------

::

    pip install scrapy-crawl-once

Usage
-----

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

request.meta interface
~~~~~~~~~~~~~~~~~~~~~~

By default the middlewares do nothing.

To avoid crawling a particular page multiple times set
``request.meta['crawl_once'] = True``. When a response
is received and a callback is successful, the fingerprint of such request
is stored to a database. When spider schedules a new request middleware
first checks if its fingerprint is in the database, and drops the request
if it is there.

Other ``request.meta`` keys:

* ``crawl_once_value`` - a value to store in DB. By default, timestamp
  is stored.
* ``crawl_once_key`` - request unique id; by default request_fingerprint
  is used.

Manual mode
~~~~~~~~~~~

To get more control over whether to add a link as seen or not (recrawl it in
future or not), scrapy-crawl-once allows to access the requests DB directly::

    import scrapy
    from scrapy_crawl_once import CrawlOnceDB

    class MySpider(scrapy.Spider):
        # ...

        def parse(self, response):
            # ... compute url
            yield scrapy.Request(url, self.parse_foo, meta={'crawl_once': True})

        def parse_foo(self, response, db: CrawlOnceDB):
            # here you can add request to DB conditionally,
            # after it is downloaded. E.g. allow to recrawl it
            # only if "unavailable" text is present on a page:

            if "unavailable" not in response.text.lower():
                db.mark_seen(response.request)

            # ...

Note how ``CrawlOnceDB`` is requested in a callback - you just need
to define a callback argument of type CrawlOnceDB.

If ``CrawlOnceDB`` is requested in a callback, scrapy-crawl-once
doesn't mark request as seen automatically; ``db.mark_seen`` method should
be called (or not called) explicitly in the callback.

If a callback has ``CrawlOnceDB``-typed argument, but a request was not sent
with ``meta={'crawl_once': True}``, then the request is not checked against
duplication database, but the DB itself still can be accessed in the callback.

Settings
--------

* ``CRAWL_ONCE_ENABLED`` - set it to False to disable middleware.
  Default is True.
* ``CRAWL_ONCE_PATH`` - a path to a folder with crawled requests database.
  By default ``.scrapy/crawl_once/`` path inside a project dir is used;
  this folder contains ``<spider_name>.sqlite`` files with databases of
  seen requests.
* ``CRAWL_ONCE_DEFAULT`` - default value for ``crawl_once`` meta key
  (False by default). When True, all requests are handled by
  this middleware unless disabled explicitly using
  ``request.meta['crawl_once'] = False``.

Alternatives
------------

https://github.com/scrapy-plugins/scrapy-deltafetch is a similar package; it
does almost the same. Differences:

* scrapy-deltafetch chooses whether to discard a request or not based on
  yielded items; scrapy-crawl-once uses an explicit
  ``request.meta['crawl_once']`` flag.
* scrapy-crawl-once allows to access the fingerprint database,
  and implement arbitrary logic for deduplication.
* scrapy-deltafetch uses bsddb3, scrapy-crawl-once uses sqlite;
  in practice sqlite is more resilient - bsddb3 can be easily corrupted if
  a spider is killed.

Another alternative is a built-in `Scrapy HTTP cache`_. Differences:

* scrapy cache stores all pages on disc, scrapy-crawl-once only keeps request
  fingerprints;
* scrapy cache allows a more fine grained invalidation consistent with how
  browsers work;
* with scrapy cache all pages are still processed (though not all pages are
  downloaded).

.. _Scrapy HTTP cache: https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#module-scrapy.downloadermiddlewares.httpcache

Contributing
------------

* source code: https://github.com/TeamHG-Memex/scrapy-crawl-once
* bug tracker: https://github.com/TeamHG-Memex/scrapy-crawl-once/issues

To run tests, install tox_ and run ``tox`` from the source checkout.

.. _tox: https://tox.readthedocs.io/en/latest/

----

.. image:: https://hyperiongray.s3.amazonaws.com/define-hg.svg
    :target: https://www.hyperiongray.com/?pk_campaign=github&pk_kwd=scrapy-crawl-once
    :alt: define hyperiongray
