# nutriapp/models/dish.py
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    recipe_text = Column(String, nullable=True)
    youtube_url = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="dishes")
    items = relationship(
        "DishItem",
        back_populates="dish",
        cascade="all, delete-orphan",
    )
    meal_entries = relationship("MealEntry", back_populates="dish")
    diet_meals = relationship("DietMeal", back_populates="dish")