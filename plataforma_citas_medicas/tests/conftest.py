import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from models import db
from utils import seed_doctors


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"check_same_thread": False}},
            "SECRET_KEY": "test-secret",
            "SEED_DEMO_DATA": False,
        }
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_doctors(db.session)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
