import os
import threading

import pytest

from app import create_app, db
from app.models import Booking, Museum, TicketType

# This test needs a real PostgreSQL database, because SQLite does not
# behave the same way under concurrent writes.
DATABASE_URL = os.environ.get("DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith("postgresql"),
    reason="Requires PostgreSQL. Set DATABASE_URL to run this test.",
)


def test_concurrent_requests_cannot_oversell_last_ticket():
    # Warning: this test drops and recreates all tables in DATABASE_URL.
    # Only point it at a development or test database.
    app = create_app({"TESTING": True})

    with app.app_context():
        db.drop_all()
        db.create_all()
        museum = Museum(name="Concurrency Test Museum", city="Amsterdam")
        # Capacity of 1: exactly one request should succeed.
        museum.ticket_types = [
            TicketType(name="Adult", price_cents=2000, capacity=1)
        ]
        db.session.add(museum)
        db.session.commit()

    attempts = 10
    # The barrier makes every thread wait until all are ready,
    # then releases them together so their requests overlap.
    barrier = threading.Barrier(attempts)
    status_codes = []
    lock = threading.Lock()

    def buy_ticket():
        client = app.test_client()
        barrier.wait()
        response = client.post(
            "/bookings",
            json={"ticket_type_id": 1, "quantity": 1, "customer_email": "a@b.com"},
        )
        with lock:
            status_codes.append(response.status_code)

    threads = [threading.Thread(target=buy_ticket) for _ in range(attempts)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    with app.app_context():
        sold = db.session.get(TicketType, 1).sold
        booking_count = Booking.query.count()
        # Close this session first. Otherwise its open transaction holds locks
        # and drop_all below waits forever.
        db.session.remove()
        db.drop_all()

    assert status_codes.count(201) == 1, f"status codes: {status_codes}"
    assert status_codes.count(409) == attempts - 1, f"status codes: {status_codes}"
    assert sold == 1
    assert booking_count == 1