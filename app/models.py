from datetime import datetime, timezone

from app import db


class Museum(db.Model):
    __tablename__ = "museums"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(80), nullable=False)

    # A museum can have many ticket types (adult, child, ...).
    ticket_types = db.relationship(
        "TicketType", backref="museum", cascade="all, delete-orphan"
    )


class TicketType(db.Model):
    __tablename__ = "ticket_types"

    id = db.Column(db.Integer, primary_key=True)
    museum_id = db.Column(db.Integer, db.ForeignKey("museums.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    # Prices are stored in cents (integers) to avoid floating-point rounding errors.
    price_cents = db.Column(db.Integer, nullable=False)
    # capacity: total number of tickets that can be sold. sold: tickets sold so far.
    capacity = db.Column(db.Integer, nullable=False)
    sold = db.Column(db.Integer, nullable=False, default=0)

    @property
    def available(self):
        return self.capacity - self.sold


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    ticket_type_id = db.Column(
        db.Integer, db.ForeignKey("ticket_types.id"), nullable=False
    )
    customer_email = db.Column(db.String(254), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_cents = db.Column(db.Integer, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
