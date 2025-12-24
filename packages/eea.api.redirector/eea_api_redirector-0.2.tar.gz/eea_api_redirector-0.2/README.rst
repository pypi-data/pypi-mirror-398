==========================
eea.api.redirector
==========================
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.api.redirector/develop
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.api.redirector/job/develop/display/redirect
  :alt: Develop
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.api.redirector/master
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.api.redirector/job/master/display/redirect
  :alt: Master

The eea.api.redirector is a Plone add-on that extends Plone's native redirect system with Redis-based URL redirects, enabling high-performance redirect lookups and external redirect management.

.. contents::


Main features
=============

1. **Redis-backed redirects**: Store and retrieve URL redirects from Redis in addition to Plone's database
2. **REST API endpoints**: Full CRUD operations for managing redirects via ``@redirects`` endpoint
3. **Control panel integration**: Web UI for managing redirects (requires `volto-redirector <https://github.com/eea/volto-redirector>`_ frontend)
4. **High-performance statistics**: Redis pipelining for calculating statistics on 100k+ redirects in ~2 seconds
5. **Advanced search**: Search both old and new URLs using simple or regex patterns (e.g., ``^/publications``, ``example.com``)
6. **Fallback mechanism**: Automatically checks Redis when redirects are not found in Plone storage
7. **Graceful error handling**: Redis connection failures don't break the redirection system
8. **API endpoint support**: Intelligent hierarchical URL matching for API services and endpoints
9. **Proper HTTP status codes**: Returns 410 Gone for permanently deleted resources (empty redirect targets)
10. **Redirect loop prevention**: Built-in protection against circular redirects
11. **Easy configuration**: Simple environment variable setup for Redis connections
12. **CSV import endpoint**: Upload CSV files directly to the backend for bulk imports
13. **Non-intrusive**: Extends existing Plone functionality without replacing it


Install
=======

* Via pip::

    $ pip install eea.api.redirector

* Or via docker-compose::

    $ docker-compose up -d

This will start both Plone 6 and Redis services with the add-on pre-configured.

* Install *eea.api.redirector* within Site Setup > Add-ons


Configuration
=============

Redis connection settings are configured via environment variables:

* ``REDIS_SERVER`` - Redis server hostname (default: ``localhost``)
* ``REDIS_PORT`` - Redis server port (default: ``6379``)
* ``REDIS_DB`` - Redis database index (default: ``0``)
* ``REDIS_TIMEOUT`` - Connection timeout in seconds (default: ``5``)

The included ``docker-compose.yml`` demonstrates how to configure these settings. The Plone service connects to Redis using::

    environment:
      REDIS_SERVER: "redis"
      REDIS_PORT: "6379"
      REDIS_DB: "0"
      REDIS_TIMEOUT: "5"


How it works
============

The add-on extends Plone's built-in ``plone.app.redirector`` by:

1. **Storage Integration**: Adds a Redis storage utility alongside Plone's database storage
2. **Fallback Lookup**: When a redirect is not found in Plone's database, it checks Redis
3. **API Support**: Custom error handling for API endpoints with hierarchical URL matching
4. **Non-blocking**: If Redis is unavailable, the system continues using Plone's standard redirects

This design allows you to:

* Manage redirects externally via Redis while maintaining Plone's UI-based redirect management
* Share redirects across multiple Plone instances using a common Redis server
* Achieve faster redirect lookups for high-traffic sites
* Store temporary or dynamic redirects that don't need to persist in Plone's database


REST API Endpoints
==================

The add-on provides REST API endpoints for managing redirects:

**GET /@redirects**

List redirects with pagination and search support.

Query parameters:

* ``q`` - Search query for old or new URL paths (supports regex: ``^/publications``, ``.*\.pdf$``)
* ``b_size`` - Batch size (default: 25, options: 10, 25, 50, 100, 500, 1000)
* ``b_start`` - Batch start offset (default: 0)
* ``search_scope`` - Where to search: ``old_url`` (default), ``new_url``, or ``both``

Example::

    GET /Plone/@redirects?q=/themes&b_size=25&b_start=0&search_scope=old_url

Response::

    {
      "@id": "http://localhost:8080/Plone/@redirects",
      "items": [
        {
          "path": "/old-path",
          "redirect-to": "/new-path"
        },
        {
          "path": "/deleted-page",
          "redirect-to": ""
        }
      ],
      "items_total": 187520
    }

**GET /@redirects-statistics**

Get statistics for redirects.

Query parameters:

* ``q`` - Optional search query to filter statistics

Example::

    GET /Plone/@redirects-statistics?q=/themes

Response::

    {
      "@id": "http://localhost:8080/Plone/@redirects-statistics",
      "statistics": {
        "total": 187520,
        "internal": 32935,
        "external": 1611,
        "gone": 152974
      }
    }

Statistics categories:

* **total** - Total number of redirects
* **internal** - Redirects to internal paths (starting with ``/``)
* **external** - Redirects to external URLs (starting with ``http://`` or ``https://``)
* **gone** - Empty redirects for permanently deleted content (HTTP 410)

**POST /@redirects**

Add new redirects.

Request body::

    {
      "items": [
        {
          "path": "/old-path",
          "redirect-to": "/new-path"
        },
        {
          "path": "/deleted-page",
          "redirect-to": ""
        }
      ]
    }

Notes:

* Empty ``redirect-to`` marks content as permanently deleted (returns HTTP 410 Gone)
* Paths are automatically trimmed of whitespace
* Self-redirects are prevented (path cannot equal redirect-to)

Response::

    {
      "success": 2,
      "failed": []
    }

**DELETE /@redirects**

Remove redirects.

Request body::

    {
      "items": [
        {"path": "/old-path"}
      ]
    }

Response::

    {
      "success": 1,
      "failed": []
    }

**POST /@redirects-import**

Import redirects from a CSV file upload.

Request:

* Multipart form-data with ``file`` field containing the CSV file

Example::

    curl -u admin:admin -F "file=@redirects.csv" http://localhost:8080/Plone/@redirects-import

Response::

    {
      "type": "success",
      "success_count": 10,
      "failed_count": 0,
      "failed": []
    }


Performance
===========

The add-on uses Redis pipelining for optimal performance:

* **Statistics calculation**: ~2 seconds for 187,000 redirects (42x faster than individual GET operations)
* **List pagination**: Scans keys only, fetches values only for requested page
* **Search queries**: Uses Redis SCAN with pattern matching for efficient filtering

Benchmark results (187,520 redirects):

* SCAN all keys: 0.36s
* Statistics with pipelining: 1.8s
* Individual GET operations: 77s (not used)


HTTP 410 Gone Support
=====================

Redirects with empty targets (``redirect-to: ""``) return HTTP 410 Gone status, indicating the resource has been permanently deleted. This is the proper HTTP status code for removed content that will not return.

The frontend (`volto-redirector <https://github.com/eea/volto-redirector>`_) can display a custom 410 Gone page with:

* Information about the deleted resource
* Link to Wayback Machine for archived versions
* Helpful navigation options


Source code
===========

- `eea.api.redirector (backend) <https://github.com/eea/eea.api.redirector>`_
- `volto-redirector (frontend) <https://github.com/eea/volto-redirector>`_


Eggs repository
===============

- https://pypi.python.org/pypi/eea.api.redirector
- http://eggrepo.eea.europa.eu/simple


Plone versions
==============
It has been developed and tested for Plone 6. See section above.


How to contribute
=================
See the `contribution guidelines (CONTRIBUTING.md) <https://github.com/eea/eea.api.redirector/blob/master/CONTRIBUTING.md>`_.

Copyright and license
=====================

eea.api.redirector (the Original Code) is free software; you can
redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc., 59
Temple Place, Suite 330, Boston, MA 02111-1307 USA.

The Initial Owner of the Original Code is European Environment Agency (EEA).
Portions created by Eau de Web are Copyright (C) 2009 by
European Environment Agency. All Rights Reserved.


Funding
=======

EEA_ - European Environment Agency (EU)

.. _EEA: https://www.eea.europa.eu/
.. _`EEA Web Systems Training`: http://www.youtube.com/user/eeacms/videos?view=1
