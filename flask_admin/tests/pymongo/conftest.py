import os

import pytest
from pymongo import MongoClient

from flask_admin import Admin


@pytest.fixture
def db(mongo_container):
    """
    PyMongo database fixture.
    Uses mongo_container from parent conftest (testcontainer or CI service).
    """
    # Prefer full connection URL (testcontainer with auth) over host-only (CI without auth)
    connection_url = os.getenv("MONGODB_CONNECTION_URL")
    if connection_url:
        client: MongoClient = MongoClient(connection_url)
    else:
        # Fallback to host-only mode for CI or manual testing
        client: MongoClient = MongoClient(
            host=os.getenv("MONGOCLIENT_HOST", "localhost")
        )

    db = client.tests
    yield db

    # Cleanup: drop test database and close connection
    client.drop_database("tests")
    client.close()


@pytest.fixture
def admin(app, babel, db):
    admin = Admin(app)
    yield admin
