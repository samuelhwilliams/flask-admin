import pytest

from flask_admin import Admin


@pytest.fixture
def admin(app, babel):
    admin = Admin(app)
    yield admin
