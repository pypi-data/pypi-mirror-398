import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    ARRAY,
    TIMESTAMP,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prism_models.base import BaseModel
from prism_models.chat import Contact, ConversationMessage
from prism_models.content import Chunk, Document

# MessageFeedback model removed - using new Feedback model below


class FeedbackType(str, enum.Enum):
    THUMBS_DOWN = "thumbs_down"
    CORRECTION = "correction"
    ENHANCEMENT = "enhancement"
    DELETION = "deletion"
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    TONE_ISSUE = "tone_issue"
    PERMISSION_ISSUE = "permission_issue"


class FeedbackStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"


class AugmentationAction(str, enum.Enum):
    CREATE = "create"
    CORRECT = "correct"
    ENHANCE = "enhance"
    DELETE = "delete"


class AugmentationStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, enum.Enum):
    CONTENT_ANALYSIS = "content_analysis"
    IMPACT_ASSESSMENT = "impact_assessment"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"


class FeedbackChunkUpdateStatus(str, enum.Enum):
    """Status of the chunk update."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FeedbackChunkUpdateType(str, enum.Enum):
    """Type of chunk update."""

    NONE = "none"
    MODIFY = "modify"
    CREATE = "create"
    DELETE = "delete"


class FeedbackChunkUpdateSource(str, enum.Enum):
    CITATION = "citation"
    AGENT_RETRIEVAL = "agent_retrieval"
    AGENT_GENERATION = "agent_generation"
    USER_MANUAL = "user_manual"


class Feedback(BaseModel):
    message_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("conversation_message.id"),
        nullable=True,
        index=True,
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(String(50), nullable=False)

    correction: Mapped[str | None] = mapped_column(Text)
    status: Mapped[FeedbackStatus] = mapped_column(
        String(50), default=FeedbackStatus.PENDING, nullable=False, index=True
    )
    admin_notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    message: Mapped[Optional["ConversationMessage"]] = relationship()

    analysis: Mapped[list["FeedbackAnalysis"]] = relationship(
        back_populates="feedback", cascade="all, delete-orphan"
    )
    augmentations: Mapped[list["Augmentation"]] = relationship(
        back_populates="feedback", cascade="all, delete-orphan"
    )
    chunk_updates: Mapped[list["FeedbackChunkUpdate"]] = relationship(
        back_populates="feedback", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Feedback(id={self.id}, type='{self.feedback_type}', status='{self.status}')>"


class FeedbackAnalysis(BaseModel):
    __tablename__ = "feedback_analysis"
    feedback_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feedback.id"), nullable=False, index=True
    )
    # raw response from the LLM
    llm_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    agent_message: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    approved: Mapped[bool] = mapped_column(Boolean, default=None, nullable=True)

    # Relationships
    feedback: Mapped["Feedback"] = relationship(back_populates="analysis")

    def __repr__(self):
        return f"<FeedbackAnalysis(id={self.id}, feedback_id={self.feedback_id})>"


class Augmentation(BaseModel):
    feedback_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feedback.id"), nullable=False, index=True
    )
    original_chunk_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chunk.id"), nullable=True
    )
    generated_chunk_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chunk.id"), nullable=True
    )
    # Relationships
    feedback: Mapped["Feedback"] = relationship(back_populates="augmentations")
    original_chunk: Mapped[Optional["Chunk"]] = relationship(
        foreign_keys=[original_chunk_id]
    )
    generated_chunk: Mapped[Optional["Chunk"]] = relationship(
        foreign_keys=[generated_chunk_id]
    )

    def __repr__(self):
        return f"<Augmentation(id={self.id})>"


class FeedbackChunkUpdate(BaseModel):
    __tablename__ = "feedback_chunk_update"

    feedback_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feedback.id"), nullable=False, index=True
    )
    chunk_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chunk.id"), nullable=True, index=True
    )
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("document.id"), nullable=True, index=True
    )

    update_type: Mapped[FeedbackChunkUpdateType] = mapped_column(
        String(50), nullable=False, default=FeedbackChunkUpdateType.MODIFY
    )
    new_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_text_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[FeedbackChunkUpdateStatus | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        index=True,
    )

    source: Mapped[FeedbackChunkUpdateSource] = mapped_column(
        String(50), nullable=False, default=FeedbackChunkUpdateSource.CITATION
    )
    marked_irrelevant: Mapped[bool] = mapped_column(Boolean, default=False)

    updated_in_analysis_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("feedback_analysis.id"), nullable=True
    )

    action_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    feedback: Mapped["Feedback"] = relationship(back_populates="chunk_updates")
    chunk: Mapped[Optional["Chunk"]] = relationship(foreign_keys=[chunk_id])
    document: Mapped[Optional["Document"]] = relationship(foreign_keys=[document_id])
    updated_in_analysis: Mapped[Optional["FeedbackAnalysis"]] = relationship(
        foreign_keys=[updated_in_analysis_id]
    )

    __table_args__ = (
        UniqueConstraint("feedback_id", "chunk_id", name="uq_feedback_chunk_update"),
    )

    def __repr__(self):
        return f"<FeedbackChunkUpdate(id={self.id}, feedback_id={self.feedback_id}, chunk_id={self.chunk_id}, type='{self.update_type}')>"
