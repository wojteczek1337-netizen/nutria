# nutriapp/models/diet_plan.py
from datetime import datetime, date

from sqlalchemy import (
    Column,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    String,
    CheckConstraint,
    Float,
    Boolean,
)
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class DietPlan(Base):
    """
    Szablon diety:
    - nazwa, opis,
    - liczba dni w cyklu (cycle_length),
    - liczba dni do przodu w kalendarzu (calendar_days),
    - początek cyklu (cycle_start_date, cycle_start_day),
    - flaga aktywna / nieaktywna.
    """
    __tablename__ = "diet_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # ile dni ma szablon diety (np. 7/14/20)
    cycle_length = Column(Integer, nullable=False, default=7)

    # ile dni planu utrzymujemy w kalendarzu do przodu
    calendar_days = Column(Integer, nullable=False, default=7)

    # data rozpoczęcia cyklu (dzień kalendarza, który odpowiada cycle_start_day)
    cycle_start_date = Column(Date, nullable=True)

    # numer dnia cyklu, od którego zaczynamy (1..cycle_length)
    cycle_start_day = Column(Integer, nullable=False, default=1)

    is_active = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    days = relationship(
        "DietDay",
        back_populates="diet",
        cascade="all, delete-orphan",
    )


class DietDay(Base):
    """
    Dzień w diecie (1..cycle_length).
    """
    __tablename__ = "diet_days"

    id = Column(Integer, primary_key=True, index=True)
    diet_id = Column(Integer, ForeignKey("diet_plans.id"), index=True, nullable=False)
    day_number = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "day_number >= 1",
            name="diet_day_number_positive",
        ),
    )

    diet = relationship("DietPlan", back_populates="days")
    meals = relationship(
        "DietMeal",
        back_populates="day",
        cascade="all, delete-orphan",
    )


class DietMeal(Base):
    """
    Posiłek w danym dniu diety (odniesienie do produktu lub dania).
    """
    __tablename__ = "diet_meals"

    id = Column(Integer, primary_key=True, index=True)
    diet_day_id = Column(Integer, ForeignKey("diet_days.id"), index=True, nullable=False)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True, index=True)

    amount_g = Column(Float, nullable=True)
    servings = Column(Float, nullable=True, default=1.0)

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
            name="diet_meal_one_food_source",
        ),
    )

    day = relationship("DietDay", back_populates="meals")
    product = relationship("Product", back_populates="diet_meals")
    dish = relationship("Dish", back_populates="diet_meals")