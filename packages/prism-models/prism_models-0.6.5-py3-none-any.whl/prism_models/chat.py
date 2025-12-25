import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, CheckConstraint, Column, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prism_models.base import BaseModel, ChatSchemaMixin


class Gender(PyEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class ContactStatus(PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    MERGED = "MERGED"


class ContactSource(PyEnum):
    GRID = "GRID"
    CRM = "CRM"
    EXTERNAL = "EXTERNAL"
    MICROSOFT_AD = "MICROSOFT_AD"


class ContactRole(PyEnum):
    """
    Hierarchical permission roles for contacts.

    Permission hierarchy (highest to lowest):
    - ADMIN: Full access to all contacts in the system
    - ACCOUNT_ADMIN: Full access to contacts within their account
    - MANAGER: Can view/edit contacts in their team (direct reports)
    - VIEWER: Read-only access to own data and limited team visibility
    """
    ADMIN = "ADMIN"
    ACCOUNT_ADMIN = "ACCOUNT_ADMIN"
    MANAGER = "MANAGER"
    VIEWER = "VIEWER"


class ConversationType(PyEnum):
    TRAVEL_GUIDE = "TRAVEL_GUIDE"
    MSA_CHAT = "MSA_CHAT"
    FEEDBACK = "FEEDBACK"


class MessageRole(PyEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class MessageStatus(PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MessageType(PyEnum):
    TEXT = "TEXT"


class MessageVote(PyEnum):
    UPVOTE = "UPVOTE"
    DOWNVOTE = "DOWNVOTE"


class Contact(ChatSchemaMixin, BaseModel):
    """
    Contact model for chat participants.

    Represents individuals who can participate in conversations within the chat system.
    Each contact can have multiple conversations and maintains their profile information
    including personal details and CRM integration data.

    Relationships:
        - conversations: One-to-many relationship with Conversation model
        - user_preferences: One-to-one relationship with UserPreferences model
    """

    email = Column(String(300), nullable=True)

    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)

    primary_phone = Column(String(45), nullable=True)

    gender: Mapped[Gender | None] = mapped_column(Enum(Gender), nullable=True)

    status: Mapped[ContactStatus | None] = mapped_column(Enum(ContactStatus), nullable=True)
    source: Mapped[ContactSource] = mapped_column(Enum(ContactSource), nullable=False)

    grid_contact_id = Column(Integer, nullable=True)

    crm_contact_guid = Column(String(36), nullable=True)

    account_id = Column(String(36), nullable=True)
    
    # oid claim from Azure AD
    azure_ad_object_id = Column(String(36), nullable=True, unique=True, index=True)
    azure_ad_tenant_id = Column(String(36), nullable=True, index=True)

    # Hierarchical permission system
    contact_role: Mapped[ContactRole] = mapped_column(
        Enum(ContactRole),
        default=ContactRole.VIEWER,
        nullable=False,
        server_default="VIEWER"
    )
    manager_contact_id = Column(
        Integer,
        ForeignKey("contact.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Self-referential relationship for hierarchy
    manager = relationship(
        "Contact",
        remote_side="Contact.id",
        foreign_keys=[manager_contact_id],
        backref="direct_reports"
    )

    conversations = relationship("Conversation", back_populates="contact", cascade="all, delete-orphan")

    # preferences relationship
    preferences: Mapped["UserPreferences"] = relationship(
        "UserPreferences",
        back_populates="contact",
        cascade="all, delete-orphan",
        uselist=False  # One-to-one relationship
    )


class UserPreferences(BaseModel):
    """
    Stores user preferences for travel recommendations.

    Single source of truth per contact - continuously updated as new preferences
    are extracted from conversations. Preferences are merged and deduplicated
    to maintain the most up-to-date view of user preferences.
    """

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key - one record per contact (UNIQUE constraint)
    contact_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contact.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Extracted preferences (JSONB for flexibility)
    likes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    dislikes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    facts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    plans: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")

    # Extraction metadata
    total_extractions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    # Relationship
    contact: Mapped["Contact"] = relationship("Contact", back_populates="preferences")

    # Indexes
    __table_args__ = (
        Index("ix_userpreferences_contact", "contact_id"),
        Index("ix_userpreferences_updated", "updated_at"),
    )


class Conversation(ChatSchemaMixin, BaseModel):
    """
    Conversation model for chat sessions.

    Represents a conversation thread between a contact and the system.
    Each conversation contains multiple messages and maintains session state.

    Relationships:
        - contact: Many-to-one relationship with Contact model
        - messages: One-to-many relationship with ConversationMessage model
    """

    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=True)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    conversation_type: Mapped[ConversationType] = mapped_column(Enum(ConversationType), nullable=False)

    is_audio_analysis = Column(Boolean, default=False, nullable=False)

    profile_id = Column(Integer, ForeignKey("profile.id"), nullable=True)
    preview_mode = Column(Boolean, default=False, nullable=False)

    # Storage links for simulation artifacts (optional)
    audio_file_url = Column(String(1024), nullable=True)
    transcription_json_url = Column(String(1024), nullable=True)
    repaired_json_url = Column(String(1024), nullable=True)

    contact = relationship("Contact", back_populates="conversations")
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    conversation_comparisons = relationship(
        "ConversationCompare",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationCompare.question_index",
    )

    profile = relationship("Profile")


class ConversationMessage(ChatSchemaMixin, BaseModel):
    """
    ConversationMessage model for individual chat messages.

    Represents individual messages within a conversation thread. Messages are ordered
    by sequence number and can be from users, assistants, or system. Each message
    tracks its processing status and can contain LLM response data.

    Relationships:
        - conversation: Many-to-one relationship with Conversation model
        - message_metadata: One-to-one relationship with ConversationMessageMetadata model

    Constraints:
        - Unique constraint on (conversation_id, sequence_number) ensures proper ordering
        - Check constraint ensures sequence_number >= 0
    """

    content = Column(Text, nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversation.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), default=MessageStatus.COMPLETED, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    sequence_number = Column(
        Integer,
        CheckConstraint("sequence_number >= 0", name="ck_sequence_number_non_negative"),
        nullable=False,
    )
    llm_response_data = Column(JSONB(), nullable=True)
    vote: Mapped[MessageVote | None] = mapped_column(Enum(MessageVote), nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    message_metadata = relationship(
        "ConversationMessageMetadata",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan",
    )
    components = relationship(
        "MessageComponent",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageComponent.position",
    )

    __table_args__ = (
        Index(
            "ix_conversation_message_conversation_sequence",
            "conversation_id",
            "sequence_number",
        ),
        Index(
            "ix_conversation_message_conversation_created",
            "conversation_id",
            "created_at",
        ),
        Index(
            "ix_conversation_message_llm_response_gin",
            "llm_response_data",
            postgresql_using="gin",
        ),
        UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="uq_conversation_message_sequence",
        ),
    )

    def is_user_message(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """Check if message is from AI assistant."""
        return self.role == MessageRole.ASSISTANT

    def is_system_message(self) -> bool:
        """Check if message is a system message."""
        return self.role == MessageRole.SYSTEM

    def is_completed(self) -> bool:
        """Check if message processing is completed."""
        return self.status == MessageStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if message processing failed."""
        return self.status == MessageStatus.FAILED


class MessageComponent(ChatSchemaMixin, BaseModel):
    """
    MessageComponent represents a UI-renderable block (e.g., entry requirement, place list)
    attached to a single ConversationMessage.
    Allows each message to contain one or more UI components, rendered in order.
    """

    component_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB(), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversation_message.id", ondelete="CASCADE"),
        nullable=False,
    )

    message = relationship("ConversationMessage", back_populates="components")

    __table_args__ = (
        Index("ix_message_component_message_id", "message_id"),
        Index("ix_message_component_position", "message_id", "position"),
        UniqueConstraint(
            "message_id",
            "position",
            name="uq_message_component_position",
        ),
    )


class ConversationMessageMetadata(ChatSchemaMixin, BaseModel):
    """
    Metadata model for RAG-specific message analytics and processing information.

    Stores performance metrics, model information, and retrieval context for each message.
    This data is essential for monitoring system performance, token usage, and
    improving RAG system effectiveness.

    Relationships:
        - message: One-to-one relationship with ConversationMessage model

    Constraints:
        - Check constraints ensure non-negative values for token counts and processing time
        - Unique constraint on message_id ensures one metadata record per message
    """

    message_id = Column(Integer, ForeignKey("conversation_message.id"), nullable=False, unique=True)
    model_name = Column(String(100), nullable=True)
    token_count_input = Column(
        Integer,
        CheckConstraint("token_count_input >= 0", name="ck_token_count_input_non_negative"),
        nullable=True,
    )
    token_count_output = Column(
        Integer,
        CheckConstraint("token_count_output >= 0", name="ck_token_count_output_non_negative"),
        nullable=True,
    )
    processing_time_ms = Column(
        Integer,
        CheckConstraint("processing_time_ms >= 0", name="ck_processing_time_non_negative"),
        nullable=True,
    )
    retrieval_context = Column(JSONB(), nullable=True)

    conversation_context = Column(Text, nullable=True)

    # Relationships
    message = relationship("ConversationMessage", back_populates="message_metadata")

    __table_args__ = (
        Index(
            "ix_conversation_message_metadata_retrieval_gin",
            "retrieval_context",
            postgresql_using="gin",
        ),
    )

    def calculate_total_tokens(self) -> int:
        """Calculate total tokens used (input + output)."""
        input_tokens = self.token_count_input or 0
        output_tokens = self.token_count_output or 0
        return int(input_tokens + output_tokens)


class ConversationCompare(ChatSchemaMixin, BaseModel):
    """
    Stores a single QA comparison for a conversation:
      - the user's question (normalized),
      - the MSA agent's answer (ground truth from transcript),
      - the AI assistant's answer (simulated reply).

    Uniqueness:
      One row per (conversation_id, question_index).
    """

    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )

    question_index: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("question_index >= 0", name="ck_sim_compare_qidx_non_negative"),
        nullable=False,
    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    msa_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    msa_speaker_label: Mapped[str | None] = mapped_column(String(32), nullable=True)

    conversation = relationship("Conversation", back_populates="conversation_comparisons")

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "question_index",
            name="uq_sim_compare_conversation_qidx",
        ),
        Index(
            "ix_sim_compare_conversation_created",
            "conversation_id",
            "created_at",
        ),
        Index(
            "ix_sim_compare_conversation_sequence",
            "conversation_id",
            "question_index",
        ),
    )
