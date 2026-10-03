from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)

    products = relationship("Product", back_populates="user")
    dishes = relationship("Dish", back_populates="user")

    profile = relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
    )
    