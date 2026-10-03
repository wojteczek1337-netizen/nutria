# nutriapp/models/weight.py
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship

from nutriapp.data.database import Base


class Weight(Base):
    __tablename__ = "weights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    measured_on = Column(Date, nullable=False, index=True)
    weight_kg = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        Index(
            "ix_weights_user_measured_on_id",
            "user_id",
            "measured_on",
            "id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Weight id={self.id} user_id={self.user_id} "
            f"measured_on={self.measured_on!r} "
            f"weight_kg={self.weight_kg!r}>"
        )