# nutriapp/models/user_profile.py
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    user = relationship("User", back_populates="profile")
    
    daily_targets = relationship(
        "DailyTarget",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    name = Column(String, nullable=True)
    sex = Column(String, nullable=False)
    age_years = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(String, nullable=False)
    goal = Column(String, nullable=False)  # "maintain" / "lose" / "gain"

    # --- Tryb kalorii ---
    # "auto" / "auto_per_kg" / "manual"
    calorie_mode = Column(String, nullable=False, default="auto")

    # Algorytm do liczenia kcal (używany w "auto" i "auto_per_kg")
    # "mifflin" / "harris_benedict" / ... (później inne)
    calorie_algorithm = Column(String, nullable=False, default="mifflin")

    # ręczne kcal (używane gdy calorie_mode == "manual")
    manual_calories = Column(Float, nullable=True)

    # ręczny deficyt/nadwyżka (używane w "auto_per_kg", opcjonalnie też w "auto")
    # w kcal, np. -100, 0, +200
    calorie_adjustment = Column(Float, nullable=False, default=0.0)

    # --- Tryb makro ---
    # "per_kg" / "manual"
    macro_mode = Column(String, nullable=False, default="per_kg")

    # g/kg (używane gdy macro_mode == "per_kg")
    protein_g_per_kg = Column(Float, nullable=True)
    fat_g_per_kg = Column(Float, nullable=True)
    carbs_g_per_kg = Column(Float, nullable=True)  # może być None → „reszta z kcal"

    # g (używane gdy macro_mode == "manual")
    manual_protein_g = Column(Float, nullable=True)
    manual_fat_g = Column(Float, nullable=True)
    manual_carbs_g = Column(Float, nullable=True)