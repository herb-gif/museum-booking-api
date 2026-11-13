# Museum Ticket Booking API

A small Flask REST API for managing museums, ticket types, and bookings. Built with PostgreSQL in Docker and tested with pytest.

## Tech stack

- Python 3.12, Flask, Flask-SQLAlchemy
- PostgreSQL (via Docker Compose)
- pytest for testing

## Getting started

### Run the tests (no Docker required)

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

### Run the full stack with Docker (PostgreSQL + API)

```bash
docker compose up --build
```

The API is available at `http://localhost:5000`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/museums` | List museums |
| GET | `/museums/<id>/tickets` | List ticket types and remaining availability for a museum |
| POST | `/bookings` | Create a booking |

Example booking request:

```bash
curl -X POST http://localhost:5000/bookings \
  -H "Content-Type: application/json" \
  -d '{"ticket_type_id": 1, "quantity": 2, "customer_email": "ali@example.com"}'
```

## Project structure

```
app/
  __init__.py   # create_app factory and the shared db object
  models.py     # Museum, TicketType, Booking tables
  routes.py     # API endpoints
tests/
  conftest.py         # Test app and sample data
  test_api.py         # Endpoint tests
  test_concurrency.py # Parallel bookings against PostgreSQL (skipped without DATABASE_URL)
.github/workflows/
  ci.yml        # GitHub Actions: runs pytest against a PostgreSQL service container
```

## Booking flow

1. The client sends `ticket_type_id`, `quantity`, and `customer_email`.
2. Input is validated (integers, quantity of at least 1, valid email format).
3. Availability is checked. If there are not enough tickets, the API returns `409 Conflict`.
4. If enough tickets remain, `sold` is incremented and a `Booking` record is created.

The availability check and the `sold` update run as one conditional `UPDATE` statement, so two concurrent requests cannot both claim the last ticket.

## Known limitations and next steps

- **Concurrency test needs PostgreSQL:** `tests/test_concurrency.py` is skipped unless `DATABASE_URL` points to PostgreSQL. It drops and recreates all tables, so only point it at a development or test database. CI runs it against a PostgreSQL service container.
- **Migrations:** Tables are currently created with `create_all`. Planned: move to Flask-Migrate.
- **Authentication:** The booking endpoint is currently public.