Partridge
=========


.. image:: https://img.shields.io/pypi/v/partridge.svg
        :target: https://pypi.python.org/pypi/partridge

.. image:: https://img.shields.io/travis/remix/partridge.svg
        :target: https://travis-ci.org/remix/partridge


Partridge is python library for working with `GTFS <https://developers.google.com/transit/gtfs/>`__ feeds using `pandas <https://pandas.pydata.org/>`__ DataFrames.

The implementation of Partridge is heavily influenced by our experience at `Remix <https://www.remix.com/>`__ ingesting, analyzing, and debugging thousands of GTFS feeds from hundreds of agencies.

At the core of Partridge is a dependency graph rooted at ``trips.txt``. Disconnected data is pruned away according to this graph when reading the contents of a feed. The root node can optionally be filtered to create a view of the feed specific to your needs. It's most common to filter a feed down to specific dates (``service_id``), routes (``route_id``), or both.

.. figure:: dependency-graph.png
   :alt: dependency graph


Philosphy
---------

The design of Partridge is guided by the following principles:

- as much as possible

  - favor speed
  - allow for extension
  - succeed lazily on expensive paths
  - fail eagerly on inexpensive paths

- as little as possible

  - do anything other than efficiently read GTFS files into DataFrames
  - take an opinion on the GTFS spec

Usage
-----

.. code:: python

    import datetime
    import partridge as ptg

    path = 'path/to/sfmta-2017-08-22.zip'

    service_ids_by_date = ptg.read_service_ids_by_date(path)

    service_ids = service_ids_by_date[datetime.date(2017, 9, 25)]

    feed = ptg.feed(path, view={
        'trips.txt': {
            'service_id': service_ids,
            'route_id': '12300', # 18-46TH AVENUE
        },
    })

    assert set(feed.trips.service_id) == service_ids
    assert list(feed.routes.route_id) == ['12300']

    # Buses running the 18 - 46th Ave line use 88 stops (on September 25, 2017, at least).
    assert len(feed.stops) == 88

Features
--------

-  Surprisingly fast :)
-  Load only what you need into memory
-  Built-in support for resolving service dates
-  Easily extended to support fields and files outside the official spec
   (TODO: document this)
-  Handle nested folders and bad data in zips
-  Predictable type conversions

Installation
------------

.. code:: console

    pip install partridge

Thank You
---------

I hope you find this library useful. If you have suggestions for
improving Partridge, please open an `issue on
GitHub <https://github.com/remix/partridge/issues>`__.
