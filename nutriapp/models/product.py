# nutriapp/models/product.py
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from nutriapp.data.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    source = Column(String, nullable=False, default="manual")

    barcode = Column(String, index=True, nullable=True)
    quantity_text = Column(String, nullable=True)
    quantity_g = Column(Float, nullable=True)

    energy_kcal_100 = Column(Float, nullable=True)
    protein_100 = Column(Float, nullable=True)
    fat_100 = Column(Float, nullable=True)
    saturated_fat_100 = Column(Float, nullable=True)
    carbs_100 = Column(Float, nullable=True)
    sugar_100 = Column(Float, nullable=True)
    fiber_100 = Column(Float, nullable=True)
    salt_100 = Column(Float, nullable=True)

    ingredients_text = Column(String, nullable=True)
    allergens = Column(String, nullable=True)

    off_code = Column(String, nullable=True)
    off_last_sync_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="products")
    dish_items = relationship("DishItem", back_populates="product")
    meal_entries = relationship("MealEntry", back_populates="product")
    diet_meals = relationship("DietMeal", back_populates="product")