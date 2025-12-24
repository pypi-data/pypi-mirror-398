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
)
from sqlalchemy import desc, asc, cast, text, func

from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase

from lecrapaud.db.session import get_db
from lecrapaud.models.base import Base
from lecrapaud.models.feature_selection import (
    lecrapaud_feature_selection_association,
)


class Feature(Base):

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
    name = Column(String(50), nullable=False, unique=True)
    type = Column(String(50))

    feature_selections = relationship(
        "FeatureSelection",
        secondary=lecrapaud_feature_selection_association,
        back_populates="features",
        lazy="selectin",
    )
