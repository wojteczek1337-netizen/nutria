# nutriapp/models/daily_target.py
from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class DailyTarget(Base):
    """Snapshot celu żywieniowego dla jednego użytkownika i dnia.

    Ten model nie przechowuje zaplanowanych posiłków. Posiłki są w MealEntry.
    Istniejący snapshot nie powinien być automatycznie nadpisywany po zmianie wagi.
    """

    __tablename__ = "daily_targets"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(
        Integer,
        ForeignKey("user_profiles.id"),
        index=True,
        nullable=False,
    )
    date = Column(Date, nullable=False, index=True)

    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)

    profile = relationship("UserProfile", back_populates="daily_targets")

    __table_args__ = (
        UniqueConstraint(
            "user_profile_id",
            "date",
            name="uq_daily_target_profile_date",
        ),
    )