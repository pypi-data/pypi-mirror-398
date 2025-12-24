from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    JSON,
    ForeignKey,
    BigInteger,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy import func
from sqlalchemy.orm import relationship
from lecrapaud.models.base import Base
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


class ModelSelectionScore(Base):
    __tablename__ = f"{LECRAPAUD_TABLE_PREFIX}_model_selection_scores"

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

    # From ModelTraining
    best_params = Column(JSON)
    model_path = Column(String(255))
    training_time = Column(Integer)
    model_id = Column(
        BigInteger, ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_models.id"), nullable=False
    )
    model_selection_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_model_selections.id", ondelete="CASCADE"),
        nullable=False,
    )

    # From Score (excluding type and training_time which is already in ModelTraining)
    eval_data_std = Column(Float)
    rmse = Column(Float)
    rmse_std_ratio = Column(Float)
    mae = Column(Float)
    mape = Column(Float)
    mam = Column(Float)
    mad = Column(Float)
    mae_mam_ratio = Column(Float)
    mae_mad_ratio = Column(Float)
    r2 = Column(Float)
    bias = Column(Float)
    logloss = Column(Float)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    roc_auc = Column(Float)
    avg_precision = Column(Float)
    thresholds = Column(JSON)
    precision_at_threshold = Column(Float)
    recall_at_threshold = Column(Float)
    f1_at_threshold = Column(Float)

    # Relationships
    model = relationship("Model", lazy="selectin")
    model_selection = relationship(
        "ModelSelection", back_populates="model_selection_scores", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "model_id", "model_selection_id", name="uq_model_selection_score_composite"
        ),
    )
