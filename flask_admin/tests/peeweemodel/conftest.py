import peewee
import pytest

from flask_admin import Admin


@pytest.fixture
def db(app):
    db = peewee.SqliteDatabase(":memory:")

    yield db

    with app.app_context():
        db.close()


@pytest.fixture
def admin(app, babel, db):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"

    admin = Admin(app)
    yield admin
