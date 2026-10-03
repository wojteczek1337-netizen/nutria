# nutriapp/models/meal_calendar.py
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Boolean,
)
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class MealEntry(Base):
    __tablename__ = "meal_entries"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    entry_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=0,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )

    dish_id = Column(
        Integer,
        ForeignKey("dishes.id"),
        nullable=True,
        index=True,
    )

    amount_g = Column(
        Float,
        nullable=True,
    )

    servings = Column(
        Float,
        nullable=False,
        default=1.0,
    )

    # Czy wpis jest elementem planu dnia
    is_planned = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Czy wpis został zjedzony
    is_eaten = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Czy wpis pochodzi z diety (szablonu)
    is_diet = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    source = Column(
        String,
        nullable=False,
        default="manual",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    product = relationship("Product", back_populates="meal_entries")
    dish = relationship("Dish", back_populates="meal_entries")

    __table_args__ = (
        CheckConstraint(
            """
            (
                product_id IS NOT NULL
                AND dish_id IS NULL
            )
            OR
            (
                product_id IS NULL
                AND dish_id IS NOT NULL
            )
            """,
            name="meal_entry_one_food_source",
        ),
    )