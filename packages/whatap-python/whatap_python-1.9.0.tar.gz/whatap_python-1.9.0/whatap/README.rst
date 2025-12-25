
.. image:: https://www.whatap.io/img/common/whatap_logo_re.svg

.. _WhaTap: https://www.whatap.io/

WhaTap_ for python
==================

- Whatap allows for application performance monitoring.
- Support: WSGI,ASGI server application
- Python version : 3.7+

Installation
------------

  .. code:: bash

    $ pip install whatap-python

Application Monitoring
----------------------

Supported web frameworks such as Django, Flask, Bottle, Cherrypy, Tornado and WSGI Server Application.

Configuration
~~~~~~~~~~~~~

  .. code:: bash

    $ export WHATAP_HOME=[PATH]
    $ whatap-setting-config --host [HOST_ADDR]
                            --license [LICENSE_KEY]
                            --app_name [APPLICATION_NAME]
                            --app_process_name [APP_PROCESS_NAME]

Usage
~~~~~

  .. code:: bash

    $ whatap-start-agent [YOUR_APPLICATION_START_COMMAND]

    ...


Copyright
---------

Copyright (c) 2017 Whatap, Inc. All rights reserved.
