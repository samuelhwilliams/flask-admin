import pytest
from flask_sqlalchemy import SQLAlchemy

from flask_admin import Admin


@pytest.fixture
def db():
    db = SQLAlchemy()
    yield db


@pytest.fixture
def admin(app, babel, db, postgres_container):
    """
    GeoAlchemy admin fixture with PostgreSQL/PostGIS database.
    Uses postgres_container from parent conftest.
    """
    app.config["SQLALCHEMY_DATABASE_URI"] = postgres_container.get_connection_url()
    app.config["SQLALCHEMY_ECHO"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.app_context().push()

    admin = Admin(app)
    yield admin

    # Cleanup: drop all tables and remove session
    db.session.remove()
    db.drop_all()
