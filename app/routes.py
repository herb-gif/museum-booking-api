from flask import Blueprint, jsonify, request
from sqlalchemy import update

from app import db
from app.models import Booking, Museum, TicketType

# A blueprint groups related endpoints. create_app registers it on the app.
bp = Blueprint("api", __name__)


@bp.get("/health")
def health():
    # Simple liveness check. Load balancers and Kubernetes probes use endpoints like this.
    return jsonify(status="ok")


@bp.get("/museums")
def list_museums():
    museums = Museum.query.order_by(Museum.name).all()
    return jsonify(
        [{"id": m.id, "name": m.name, "city": m.city} for m in museums]
    )


@bp.get("/museums/<int:museum_id>/tickets")
def list_tickets(museum_id):
    museum = db.session.get(Museum, museum_id)
    if museum is None:
        return jsonify(error="museum not found"), 404

    return jsonify(
        [
            {
                "id": t.id,
                "name": t.name,
                "price_cents": t.price_cents,
                "available": t.available,
            }
            for t in museum.ticket_types
        ]
    )


@bp.post("/bookings")
def create_booking():
    # get_json(silent=True) returns None on malformed JSON instead of raising.
    data = request.get_json(silent=True) or {}
    ticket_type_id = data.get("ticket_type_id")
    quantity = data.get("quantity")
    email = data.get("customer_email", "")

    # 1) Validate input. Never trust data sent by the client.
    if not isinstance(ticket_type_id, int) or not isinstance(quantity, int):
        return jsonify(error="ticket_type_id and quantity must be integers"), 400
    if quantity < 1:
        return jsonify(error="quantity must be at least 1"), 400
    if "@" not in email:
        return jsonify(error="a valid customer_email is required"), 400

    ticket = db.session.get(TicketType, ticket_type_id)
    if ticket is None:
        return jsonify(error="ticket type not found"), 404

    # 2) Check and reserve in ONE atomic SQL statement.
    # The WHERE clause re-checks capacity inside the database, so two requests
    # cannot both claim the same last ticket.
    result = db.session.execute(
        update(TicketType)
        .where(
            TicketType.id == ticket_type_id,
            TicketType.capacity - TicketType.sold >= quantity,
        )
        .values(sold=TicketType.sold + quantity)
    )
    if result.rowcount == 0:
        # Not enough tickets: undo the transaction and reload the current count.
        db.session.rollback()
        db.session.refresh(ticket)
        return (
            jsonify(error="not enough tickets available", available=ticket.available),
            409,
        )

    # 3) Record the booking in the same transaction.
    booking = Booking(
        ticket_type_id=ticket.id,
        customer_email=email,
        quantity=quantity,
        total_cents=quantity * ticket.price_cents,
    )
    db.session.add(booking)
    db.session.commit()

    return jsonify(id=booking.id, total_cents=booking.total_cents), 201