
Installation
============

This assumes you already have a :doc:`WuttJamaican app+database
<wuttjamaican:narr/install/index>` setup and working.

Install the Wutta-Continuum package to your virtual environment:

.. code-block:: sh

   pip install Wutta-Continuum

Edit your :term:`config file` to enable Wutta-Continuum versioning:

.. code-block:: ini

   [wutta_continuum]
   enable_versioning = true

.. note::

   The above *must* be done via config file; the :term:`settings
   table` will not work.

Another edit required to your config file, is to make Alembic aware of
this package for database migrations.  You should already have an
``[alembic]`` section, but now must update it like so:

.. code-block:: ini

   [alembic]
   script_location = wuttjamaican.db:alembic
   version_locations = wutta_continuum.db:alembic/versions poser.db:alembic/versions wuttjamaican.db:alembic/versions

Then (as you would have done previously in
:ref:`wuttjamaican:db-setup`) you can migrate your database to add the
versioning tables:

.. code-block:: sh

   cd /path/to/env
   bin/alembic -c /path/to/my.conf upgrade heads

And that's it, the versioning/history feature should be setup and working.
