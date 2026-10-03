# nutriapp/models/daily_points.py
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class DailyPoints(Base):
    """Punkty jednego użytkownika za jeden dzień.

    Wiersz jest przeliczany przy wejściu na listę użytkowników i w szczegóły,
    na podstawie zjedzonych posiłków oraz zapisanego celu dnia.
    """

    __tablename__ = "daily_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    scored_on = Column(Date, nullable=False, index=True)
    calorie_points = Column(Integer, nullable=False)
    protein_points = Column(Integer, nullable=False)
    fat_points = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "scored_on",
            name="uq_daily_points_user_date",
        ),
    )

    @property
    def total_points(self) -> int:
        return self.calorie_points + self.protein_points + self.fat_points
