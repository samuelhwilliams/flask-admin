import os

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
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_container(docker_available):
    """
    Session-scoped PostGIS container for PostgreSQL tests.
    Falls back to environment variable if Docker unavailable or in CI.
    """
    # If SQLALCHEMY_DATABASE_URI is set (e.g., in CI), use that instead
    if os.getenv("SQLALCHEMY_DATABASE_URI"):
        yield None  # Use environment-provided database
        return

    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    import sqlalchemy
    from testcontainers.postgres import PostgresContainer

    # Use PostGIS image for GeoAlchemy support
    with PostgresContainer(
        image="postgis/postgis:16-3.4",
        username="postgres",
        password="postgres",
        dbname="flask_admin_test",
    ) as container:
        connection_url = container.get_connection_url()
        os.environ["SQLALCHEMY_DATABASE_URI"] = connection_url

        # Create required PostgreSQL extensions
        # (Matches what CI does in GitHub Actions workflow)
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
    Falls back to environment variable if Docker unavailable or in CI.
    """
    # If MONGOCLIENT_HOST is set (e.g., in CI), use that instead
    # CI uses service containers without auth, just host:port
    if os.getenv("MONGOCLIENT_HOST"):
        yield None  # Use environment-provided database
        return

    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    from testcontainers.mongodb import MongoDbContainer

    with MongoDbContainer(image="mongo:5.0.14-focal") as container:
        # Store full connection URL with authentication credentials
        # Format: mongodb://username:password@host:port/
        connection_url = container.get_connection_url()
        os.environ["MONGODB_CONNECTION_URL"] = connection_url

        # Also extract host for backward compatibility with CI pattern
        # In local testcontainer mode, this will be overridden by MONGODB_CONNECTION_URL
        os.environ["MONGOCLIENT_HOST"] = connection_url.split("@")[1].split("/")[0]

        yield container


@pytest.fixture(scope="session")
def azurite_container(docker_available):
    """
    Session-scoped Azurite container for Azure Blob Storage tests.
    Falls back to environment variable if Docker unavailable or in CI.
    """
    # If AZURE_STORAGE_CONNECTION_STRING is set (e.g., in CI), use that instead
    if os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
        yield None  # Use environment-provided storage
        return

    if not docker_available:
        pytest.skip("Docker not available for testcontainers")

    import time

    from testcontainers.core.container import DockerContainer

    # Azurite container for Azure Blob Storage emulation
    container = DockerContainer(image="mcr.microsoft.com/azure-storage/azurite:latest")
    container.with_exposed_ports(10000)
    container.with_command("azurite-blob --blobHost 0.0.0.0")

    container.start()

    # Give Azurite a moment to start up
    time.sleep(2)

    # Get the mapped port
    blob_port = container.get_exposed_port(10000)

    # Set standard Azurite development connection string
    connection_string = (
        f"DefaultEndpointsProtocol=http;"
        f"AccountName=devstoreaccount1;"
        f"AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        f"BlobEndpoint=http://localhost:{blob_port}/devstoreaccount1;"
    )
    os.environ["AZURE_STORAGE_CONNECTION_STRING"] = connection_string

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
