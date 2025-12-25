"""Profile model for storing user profile information."""

from datetime import datetime
from enum import Enum
from typing import Any

from prism_models.chat import Contact
from sqlalchemy import TIMESTAMP, Boolean, Index, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Text

from prism_models.base import BaseModel
from prism_models.content import Collection


class Profile(BaseModel):
    """
    Profile model for organizing prompt variants by team/use case.

    Profiles allow admins to create different prompt variations for different
    teams or scenarios (e.g., "marketing_aggressive", "support_friendly").
    Each profile allows configuration of multiple agents.

    Relationships:
        - profile_prompts: One-to-many with ProfilePrompt
        - agent_profiles: One-to-many with AgentProfile
        - conversation_profiles: One-to-many with ConversationProfile
    """

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1024))
    orchestrator_model: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default="openai:gpt-4.1"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("name", name="uq_profile_name"),)

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, name='{self.name}', active={self.is_active})>"

class AgentType(str, Enum):
    ORCHESTRATOR_AGENT = "ORCHESTRATOR"
    DOMAIN_AGENT = "DOMAIN"
    UTILITY_AGENT = "UTILITY"
    SUMMARIZER_AGENT = "SUMMARIZER"

class Agent(BaseModel):
    """Agent model for storing agent information."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1024))
    type: Mapped[AgentType] = mapped_column(SAEnum(AgentType, name="agent_type"), nullable=True)
    default_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    functions: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(), nullable=True
    )


    __table_args__ = (
        UniqueConstraint("name", name="uq_agent_name"),
        UniqueConstraint("display_name", name="uq_agent_display_name"),
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}')>"


class AgentProfileStatus(str, Enum):
    """
    @deprecated - use AgentProfileVersionStatus instead
    """
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PREVIEW = "PREVIEW"


class AgentProfile(BaseModel):
    """
    Binding between Agent and Profile.
    Determines if the agent is enabled for this profile.
    """

    agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agent.id"), nullable=False, index=True
    )
    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profile.id"), nullable=False, index=True
    )

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    versions: Mapped[list["AgentProfileVersion"]] = relationship(
        back_populates="agent_profile",
        cascade="all, delete-orphan",
        order_by="AgentProfileVersion.version.desc()"
    )
    
    created_by_contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contact.id"), nullable=True)

    agent: Mapped["Agent"] = relationship()
    profile: Mapped["Profile"] = relationship()
    created_by_contact: Mapped["Contact"] = relationship(foreign_keys=[created_by_contact_id])
    __table_args__ = (
        UniqueConstraint("agent_id", "profile_id", name="uq_agent_profile_binding"),
    )
    
class AgentProfileVersionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PREVIEW = "PREVIEW"
    ARCHIVED = "ARCHIVED"


class AgentProfileVersion(BaseModel):
    """
    Versioned behavior for an Agent within a Profile.
    Stores:
    - prompt text
    - status
    - list of enabled functions for this version
    """

    agent_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agent_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[AgentProfileVersionStatus] = mapped_column(
        SAEnum(AgentProfileVersionStatus),
        nullable=False,
        default=AgentProfileVersionStatus.PREVIEW,
    )

    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    functions_enabled: Mapped[list[str] | None] = mapped_column(JSONB(), nullable=True)
    
    agent_profile: Mapped["AgentProfile"] = relationship(back_populates="versions")

    modified_by_contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contact.id"), nullable=True)
    modified_by_contact: Mapped["Contact"] = relationship(foreign_keys=[modified_by_contact_id])

    published_by_contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contact.id"), nullable=True)
    published_by_contact: Mapped["Contact"] = relationship(foreign_keys=[published_by_contact_id])

    __table_args__ = (
        UniqueConstraint(
            "agent_profile_id", "version",
            name="uq_agent_profile_version_number",
        ),
        Index(
            "ix_agent_profile_only_one_active",
            "agent_profile_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'")
        ),

        Index(
            "ix_agent_profile_only_one_preview",
            "agent_profile_id",
            unique=True,
            postgresql_where=text("status = 'PREVIEW'")
        ),
    )



class ProfileCollectionAccess(BaseModel):
    """ProfileCollectionAccess model for storing profile collection access information."""

    profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    collection: Mapped["Collection"] = relationship()
    profile: Mapped["Profile"] = relationship()

    __table_args__ = (UniqueConstraint("profile_id", "collection_id", name="uq_profile_collection"),)


class AgentCollectionAccess(BaseModel):
    """AgentCollectionAccess model for storing agent collection information."""

    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agent.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    agent: Mapped["Agent"] = relationship()
    collection: Mapped["Collection"] = relationship()

    __table_args__ = (UniqueConstraint("agent_id", "collection_id", name="uq_agent_collection"),)
