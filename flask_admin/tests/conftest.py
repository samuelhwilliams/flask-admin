import pytest
from flask import Flask
from jinja2 import StrictUndefined

from flask_admin import Admin

# =============================================================================
# Container Fixtures (Session Scope)
# These start once per test session for performance
# =============================================================================


@pytest.fixture(scope="session")
def docker_available():
    """Check if Docker is available for testcontainers."""
    try:
        import docker  # type: ignore[import-untyped]

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_container(docker_available):
    """
    Session-scoped PostGIS container for PostgreSQL tests.
    Returns the container object; use .get_connection_url() to get connection string.
    """
    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    import sqlalchemy
    from testcontainers.postgres import (  # type: ignore[import-not-found]
        PostgresContainer,
    )

    # Use PostGIS image for GeoAlchemy support
    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        username="postgres",
        password="postgres",
        dbname="flask_admin_test",
    ) as container:
        # Create required PostgreSQL extensions
        connection_url = container.get_connection_url()
        engine = sqlalchemy.create_engine(connection_url)
        with engine.begin() as conn:
            # hstore extension - required for test_hstore
            conn.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS hstore"))
        engine.dispose()

        yield container


@pytest.fixture(scope="session")
def mongo_container(docker_available):
    """
    Session-scoped MongoDB container for MongoDB/MongoEngine tests.
    Returns the container object; use .get_connection_url() to get connection string.
    """
    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    from testcontainers.mongodb import (  # type: ignore[import-not-found]
        MongoDbContainer,
    )

    with MongoDbContainer(image="mongo:5.0.14-focal") as container:
        yield container


@pytest.fixture(scope="session")
def azurite_container(docker_available):
    """
    Session-scoped Azurite container for Azure Blob Storage tests.
    Returns the container object; use .get_connection_string() to get connection string.
    """
    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    import time

    from testcontainers.core.container import (  # type: ignore[import-not-found]
        DockerContainer,
    )

    # Azurite container for Azure Blob Storage emulation
    container = DockerContainer(image="mcr.microsoft.com/azure-storage/azurite:latest")
    container.with_exposed_ports(10000)
    container.with_command("azurite-blob --blobHost 0.0.0.0")

    container.start()

    # Give Azurite a moment to start up
    time.sleep(2)

    # Add a helper method to get the connection string
    def get_connection_string():
        blob_port = container.get_exposed_port(10000)
        return (
            f"DefaultEndpointsProtocol=http;"
            f"AccountName=devstoreaccount1;"
            f"AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
            f"BlobEndpoint=http://localhost:{blob_port}/devstoreaccount1;"
        )

    container.get_connection_string = get_connection_string

    yield container

    container.stop()


# =============================================================================
# Application Fixtures (Function Scope)
# =============================================================================


@pytest.fixture(scope="function")
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "1"
    app.config["WTF_CSRF_ENABLED"] = False
    app.jinja_env.undefined = StrictUndefined
    yield app


@pytest.fixture
def babel(app):
    babel = None
    try:
        from flask_babel import Babel

        babel = Babel(app)
    except ImportError:
        pass

    yield babel


@pytest.fixture
def admin(app, babel):
    admin = Admin(app)
    yield admin
