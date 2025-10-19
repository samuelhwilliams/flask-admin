import pytest
from mongoengine import connect
from mongoengine import disconnect
from mongoengine import get_connection

from flask_admin import Admin


@pytest.fixture
def db(mongo_container):
    """
    MongoEngine database fixture.
    Uses mongo_container from parent conftest.
    """
    db_name = "tests"
    connect(
        db=db_name,
        host=mongo_container.get_connection_url(),
        uuidRepresentation="standard",
    )

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
