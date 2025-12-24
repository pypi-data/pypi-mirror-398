from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    JSON,
    Table,
    ForeignKey,
    BigInteger,
    Index,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy import desc, asc, cast, text, func

from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase

from lecrapaud.db.session import get_db
from lecrapaud.models.base import Base
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


class ModelSelection(Base):

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    best_model_params = Column(JSON)
    best_thresholds = Column(JSON)
    best_score = Column(JSON)
    best_model_path = Column(String(255))
    best_model_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_models.id", ondelete="CASCADE"),
    )
    target_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_targets.id", ondelete="CASCADE"),
        nullable=False,
    )
    experiment_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_experiments.id", ondelete="CASCADE"),
        nullable=False,
    )

    best_model = relationship("Model", lazy="selectin")
    model_selection_scores = relationship(
        "ModelSelectionScore",
        back_populates="model_selection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    experiment = relationship(
        "Experiment", back_populates="model_selections", lazy="selectin"
    )
    target = relationship("Target", back_populates="model_selections", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "target_id", "experiment_id", name="uq_model_selection_composite"
        ),
    )
