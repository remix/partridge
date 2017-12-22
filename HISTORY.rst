History
=======

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
