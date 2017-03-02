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

By default it does nothing. To avoid crawling a particular page
multiple times set ``request.meta['crawl_once'] = True``. When a response
is received and a callback is successful, the fingerprint of such request
is stored to a database. When spider schedules a new request middleware
first checks if its fingerprint is in the database, and drops the request
if it is there.

Other ``request.meta`` keys:

* ``crawl_once_value`` - a value to store in DB. By default, timestamp
  is stored.
* ``crawl_once_key`` - request unique id; by default request_fingerprint
  is used.

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
* scrapy-deltafetch uses bsddb3, scrapy-crawl-once uses sqlite.

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
