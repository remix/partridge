History
=======

0.9.0 (2018-03-24)
------------------

* Improves read time for large feeds by adding LRU caching to ``ptg.parsers.parse_time``.


0.8.0 (2018-03-14)
------------------

* Gracefully handle completely empty files. This change unifies the behavior of reading from a CSV
with a header only (no data rows) and a completely empty (zero bytes)
file in the zip.


0.7.0 (2018-03-09)
------------------

* Fix handling of nested folders and zip containing nested folders.
* Add ``ptg.get_filtered_feed`` for multi-file filtering.


0.6.1 (2018-02-24)
------------------

* Fix bug in ``ptg.read_service_ids_by_date``. Reported by @cjer in #27.


0.6.0 (2018-02-21)
------------------

* Published package no longer includes unnecessary fixtures to reduce the size.
* Naively write a feed object to a zip file with ``ptg.write_feed_dangerously``.
* Read the earliest, busiest date and its ``service_id``'s from a feed with ``ptg.read_busiest_date``.
* Bug fix: Handle ``calendar.txt``/``calendar_dates.txt`` entries w/o applicable trips.


0.6.0.dev1 (2018-01-23)
-----------------------

* Add support for reading files from a folder. Thanks again @danielsclint!


0.5.0 (2017-12-22)
------------------

* Easily build a representative view of a zip with ``ptg.get_representative_feed``. Inspired by `peartree <https://github.com/kuanb/peartree/blob/3bfc3f49ae6986d6020913b63c8ee32582b3dcc3/peartree/paths.py#L26>`_.
* Extract out GTFS zips by agency_id/route_id with ``ptg.extract_{agencies,routes}``.
* Read arbitrary files from a zip with ``feed.get('myfile.txt')``.
* Remove ``service_ids_by_date``, ``dates_by_service_ids``, and ``trip_counts_by_date`` from the feed class. Instead use ``ptg.{read_service_ids_by_date,read_dates_by_service_ids,read_trip_counts_by_date}``.


0.4.0 (2017-12-10)
------------------

* Add support for Python 2.7. Thanks @danielsclint!


0.3.0 (2017-10-12)
------------------

* Fix service date resolution for raw_feed. Previously raw_feed considered all days of the week from calendar.txt to be active regardless of 0/1 value.


0.2.0 (2017-09-30)
------------------

* Add missing edge from fare_rules.txt to routes.txt in default dependency graph.


0.1.0 (2017-09-23)
------------------

* First release on PyPI.
