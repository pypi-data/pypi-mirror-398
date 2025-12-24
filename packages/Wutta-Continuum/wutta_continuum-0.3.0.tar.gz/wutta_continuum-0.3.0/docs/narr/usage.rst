
Usage
=====

You can check the feature status with
:meth:`~wutta_continuum.app.WuttaContinuumAppProvider.continuum_is_enabled()`::

   app = config.get_app()

   if not app.continuum_is_enabled():
       print("Oh no!  Continuum is not enabled.")

The rest of this will assume the feature is enabled.


Built-In Models
---------------

The following built-in models are versioned.  So, when records are
added / modified / removed via the ORM, new version records are
automatically created for each of these:

* :class:`~wuttjamaican:wuttjamaican.db.model.auth.Permission`
* :class:`~wuttjamaican:wuttjamaican.db.model.base.Person`
* :class:`~wuttjamaican:wuttjamaican.db.model.auth.Role`
* :class:`~wuttjamaican:wuttjamaican.db.model.auth.User`
* :class:`~wuttjamaican:wuttjamaican.db.model.auth.UserRole`


Object Versions
---------------

A versioned model works normally but also has a ``versions``
attribute, which reflects the list of version records::

    user = session.query(model.User).first()

    for version in user.versions:
        print(version)

See also :doc:`sqlalchemy-continuum:version_objects`.
