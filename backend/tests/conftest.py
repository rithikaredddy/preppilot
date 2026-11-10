import pytest

from app import create_app
from app.extensions import db


@pytest.fixture(scope="session")
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_database(app):
    yield
    with app.app_context():
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.session.remove()


@pytest.fixture(autouse=True)
def reset_login_throttle():
    from app.services import auth_service

    auth_service._failed_logins.clear()
    yield
    auth_service._failed_logins.clear()
