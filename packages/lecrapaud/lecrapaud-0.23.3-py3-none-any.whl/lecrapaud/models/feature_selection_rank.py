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
from sqlalchemy.dialects.mysql import insert

from lecrapaud.db.session import get_db
from lecrapaud.models.base import Base, with_db
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


class FeatureSelectionRank(Base):

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
    score = Column(Float)
    pvalue = Column(Float)
    support = Column(Integer)
    rank = Column(Integer)
    method = Column(String(50))
    training_time = Column(Integer)
    feature_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_features.id", ondelete="CASCADE"),
    )
    feature_selection_id = Column(
        BigInteger,
        ForeignKey(
            f"{LECRAPAUD_TABLE_PREFIX}_feature_selections.id", ondelete="CASCADE"
        ),
    )

    feature = relationship("Feature", lazy="selectin")
    feature_selection = relationship(
        "FeatureSelection", back_populates="feature_selection_ranks", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "feature_id",
            "feature_selection_id",
            "method",
            name="uq_feature_selection_rank_composite",
        ),
    )
