import pytest
from pymongo import MongoClient

from flask_admin import Admin


@pytest.fixture
def db(mongo_container):
    """
    PyMongo database fixture.
    Uses mongo_container from parent conftest.
    """
    client: MongoClient = MongoClient(mongo_container.get_connection_url())
    db = client.tests
    yield db

    # Cleanup: drop test database and close connection
    client.drop_database("tests")
    client.close()


@pytest.fixture
def admin(app, babel, db):
    admin = Admin(app)
    yield admin
