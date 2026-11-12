import pytest

from app import create_app, db
from app.models import Museum, TicketType


@pytest.fixture
def app():
    # Tests use an in-memory SQLite database instead of PostgreSQL:
    # it is fast, needs no setup, and every test starts with a clean database.
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )

    with app.app_context():
        museum = Museum(name="Rijksmuseum", city="Amsterdam")
        # Capacity of 2: two tickets can be sold, a third request must be rejected.
        museum.ticket_types = [
            TicketType(name="Adult", price_cents=2000, capacity=2)
        ]
        db.session.add(museum)
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
