
Features
========

The general idea is to provide an audit/versioning trail for important
data tables.

Each table defined in the :term:`app model` can either be versioned,
or not.  Nothing changes for a non-versioned table.

For a "versioned" table, a secondary "versions" table is created,
schema for which is a superset of the original "versioned" table.
When records change in the original table, new "version" records are
added to the versions table.

Therefore you can see how a record has changed over time, by
inspecting its corresponding versions.

When any record changes (for any versioned table), a new "transaction"
record is also created.  This identifies the user responsible, and
timestamp etc.  Any new version records will tie back to this
transaction record.

All this is made possible by SQLAlchemy-Continuum; the Wutta-Continuum
package mostly just adds config glue.  See also
:doc:`sqlalchemy-continuum:index`.
