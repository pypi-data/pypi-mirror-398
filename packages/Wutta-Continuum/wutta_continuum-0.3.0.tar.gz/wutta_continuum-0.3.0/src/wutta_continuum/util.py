# -*- coding: utf-8; -*-
################################################################################
#
#  Wutta-Continuum -- SQLAlchemy Versioning for Wutta Framework
#  Copyright © 2024-2025 Lance Edgar
#
#  This file is part of Wutta Framework.
#
#  Wutta Framework is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  Wutta Framework is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  Wutta Framework.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
"""
SQLAlchemy-Continuum utilities
"""

import sqlalchemy as sa
from sqlalchemy import orm
import sqlalchemy_continuum as continuum


OPERATION_TYPES = {
    continuum.Operation.INSERT: "INSERT",
    continuum.Operation.UPDATE: "UPDATE",
    continuum.Operation.DELETE: "DELETE",
}


def render_operation_type(operation_type):
    """
    Render a SQLAlchemy-Continuum ``operation_type`` from a version
    record, for display to user.

    :param operation_type: Value of same name from a version record.
       Must be one of:

       * :attr:`sqlalchemy_continuum:sqlalchemy_continuum.operation.Operation.INSERT`
       * :attr:`sqlalchemy_continuum:sqlalchemy_continuum.operation.Operation.UPDATE`
       * :attr:`sqlalchemy_continuum:sqlalchemy_continuum.operation.Operation.DELETE`

    :returns: Display name for the operation type, as string.
    """
    return OPERATION_TYPES[operation_type]


def model_transaction_query(instance, session=None, model_class=None):
    """
    Make a query capable of finding all SQLAlchemy-Continuum
    ``transaction`` records associated with the given model instance.

    :param instance: Instance of a versioned :term:`data model`.

    :param session: Optional :term:`db session` to use for the query.
       If not specified, will be obtained from the ``instance``.

    :param model_class: Optional :term:`data model` class to query.
       If not specified, will be obtained from the ``instance``.

    :returns: SQLAlchemy query object.  Note that it will *not* have an
       ``ORDER BY`` clause yet.
    """
    if not session:
        session = orm.object_session(instance)
    if not model_class:
        model_class = type(instance)

    txncls = continuum.transaction_class(model_class)
    vercls = continuum.version_class(model_class)

    query = session.query(txncls).join(
        vercls,
        sa.and_(vercls.uuid == instance.uuid, vercls.transaction_id == txncls.id),
    )

    return query
