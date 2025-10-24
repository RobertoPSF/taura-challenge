import pytest
from app import create_app, db

@pytest.fixture(scope="module")
def test_app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Banco em memória
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(test_app):
    return test_app.test_client()
