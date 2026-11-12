def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_list_museums(client):
    response = client.get("/museums")

    assert response.status_code == 200
    assert response.get_json()[0]["name"] == "Rijksmuseum"


def test_list_tickets_for_museum(client):
    # The first museum and ticket type created in conftest.py both have id 1.
    response = client.get("/museums/1/tickets")

    assert response.get_json() == [
        {"id": 1, "name": "Adult", "price_cents": 2000, "available": 2}
    ]


def test_unknown_museum_returns_404(client):
    response = client.get("/museums/999/tickets")

    assert response.status_code == 404


def test_booking_reduces_availability(client):
    response = client.post(
        "/bookings",
        json={"ticket_type_id": 1, "quantity": 2, "customer_email": "a@b.com"},
    )

    assert response.status_code == 201
    assert response.get_json()["total_cents"] == 4000

    tickets = client.get("/museums/1/tickets").get_json()
    assert tickets[0]["available"] == 0


def test_booking_over_capacity_is_rejected(client):
    response = client.post(
        "/bookings",
        json={"ticket_type_id": 1, "quantity": 3, "customer_email": "a@b.com"},
    )

    assert response.status_code == 409
    assert response.get_json()["available"] == 2


def test_booking_with_invalid_quantity_is_rejected(client):
    response = client.post(
        "/bookings",
        json={"ticket_type_id": 1, "quantity": 0, "customer_email": "a@b.com"},
    )

    assert response.status_code == 400


def test_booking_with_invalid_email_is_rejected(client):
    response = client.post(
        "/bookings",
        json={"ticket_type_id": 1, "quantity": 1, "customer_email": "invalid"},
    )

    assert response.status_code == 400
