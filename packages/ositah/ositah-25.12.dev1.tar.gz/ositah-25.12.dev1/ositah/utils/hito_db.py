"""
Module defining a few helper functions to access the DB through SQLAlchemy
"""

import re
from uuid import uuid4

from flask import g
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from ositah.app import app
from ositah.utils.utils import GlobalParams


def new_uuid():
    """
    Wrapper over uuid4() to return the UUID as a string. Allow using a callable in the column
    default attribute (else it is interpreted as constant and the UUID is the same for every row).

    :return: UUID string
    """
    return str(uuid4())


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if re.match("sqlite:", app.server.config["SQLALCHEMY_DATABASE_URI"]):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db(init_session: bool = True) -> None:
    """
    Return the DB handler if already initialized, else create it and initialize a DB session
    in the application context.

    :param init_session: if True initialize a session if necessary
    :return: DB handler
    """
    global_params = GlobalParams()

    with app.server.app_context():
        if "db" not in g:
            g.db = global_params.hito_db
        if init_session and not g.db.session.bind:
            g.db.session = scoped_session(sessionmaker(g.db.engine))

        return g.db
