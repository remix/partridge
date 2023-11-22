=======
History
=======

1.1.2 (2022-11-23)
------------------

Code changes:

* Remove references to deprecated NumPy types (https://github.com/remix/partridge/pull/69 - thanks @BlackSpade741!)
* Switch from `cChardet <https://github.com/PyYoshi/cChardet>`_ to `charset-normalizer <https://github.com/Ousret/charset_normalizer>`_ for Python 3.10 support (https://github.com/remix/partridge/pull/76 - thanks @brockhaywood!)

Other changes:

* Miscellaneous improvements to tests, code formatting, and documentation (https://github.com/remix/partridge/pull/61 - thanks @invisiblefunnel!)
* Relocate usage examples from wiki to README (https://github.com/remix/partridge/pull/70 - thanks @landonreed!)
* README tweaks (https://github.com/remix/partridge/pull/74 - thanks @chelsey!)
* Use GitHub Actions for automated testing (https://github.com/remix/partridge/pull/79 - thanks @dget!). **Note:** we now test against Python versions 3.8, 3.9, 3.10, and 3.11.


1.1.1 (2019-09-13)
------------------

* Improve file encoding sniffer, which was misidentifying some Finnish/emoji unicode. Thanks to @dyakovlev!


1.1.0 (2019-02-21)
------------------

* Add ``partridge.load_geo_feed`` for reading stops and shapes into GeoPandas GeoDataFrames.


1.0.0 (2018-12-18)
------------------

This release is a combination of major internal refactorings and some minor interface changes. Overall, you should expect your upgrade from pre-1.0 versions to be relatively painless. A big thank you to @genhernandez and @csb19815 for their valuable design feedback. If you still need Python 2 support, please continue using version 0.11.0.

Here is a list of interface changes:

* The class ``partridge.gtfs.feed`` has been renamed to ``partridge.gtfs.Feed``.
* The public interface for instantiating feeds is ``partridge.load_feed``. This function replaces the previously undocumented function ``partridge.get_filtered_feed``.
* A new function has been added for identifying the busiest week in a feed: ``partridge.read_busiest_date``
* The public function ``partridge.get_representative_feed`` has been removed in favor of using ``partridge.read_busiest_date`` directly.
* The public function ``partridge.writers.extract_feed`` is now available via the top level module: ``partridge.extract_feed``.

Miscellaneous minor changes:

* Character encoding detection is now done by the ``cchardet`` package instead of ``chardet``. ``cchardet`` is faster, but may not always return the same result as ``chardet``.
* Zip files are unpacked into a temporary directory instead of reading directly from the zip. These temporary directories are cleaned up when the feed is garbage collected or when the process exits.
* The code base is now annotated with type hints and the build runs ``mypy`` to verify the types.
* DataFrames are cached in a dictionary instead of the ``functools.lru_cache`` decorator.
* The ``partridge.extract_feed`` function now writes files concurrently to improve performance.


0.11.0 (2018-08-01)
-------------------

* Fix major performance issue related to encoding detection. Thank you to @cjer for reporting the issue and advising on a solution.


0.10.0 (2018-04-30)
-------------------

* Improved handling of non-standard compliant file encodings
* Only require functools32 for Python < 3
* ``ptg.parsers.parse_date`` no longer accepts dates, only strings


0.9.0 (2018-03-24)
------------------

* Improves read time for large feeds by adding LRU caching to ``ptg.parsers.parse_time``.


0.8.0 (2018-03-14)
------------------

* Gracefully handle completely empty files. This change unifies the behavior of reading from a CSV with a header only (no data rows) and a completely empty (zero bytes) file in the zip.


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
