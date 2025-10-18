import os

import pytest
from mongoengine import connect
from mongoengine import disconnect
from mongoengine import get_connection

from flask_admin import Admin


@pytest.fixture
def db(mongo_container):
    """
    MongoEngine database fixture.
    Uses mongo_container from parent conftest (testcontainer or CI service).
    """
    db_name = "tests"

    # Prefer full connection URL (testcontainer with auth) over host-only (CI without auth)
    connection_url = os.getenv("MONGODB_CONNECTION_URL")
    if connection_url:
        connect(db=db_name, host=connection_url, uuidRepresentation="standard")
    else:
        # Fallback to host-only mode for CI or manual testing
        host = os.getenv("MONGOCLIENT_HOST", "localhost")
        connect(db=db_name, host=host, uuidRepresentation="standard")

    yield db_name

    # Cleanup: drop test database and disconnect
    try:
        connection = get_connection()
        connection.drop_database(db_name)
    finally:
        disconnect()


@pytest.fixture
def admin(app, babel, db):
    admin = Admin(app)
    yield admin
