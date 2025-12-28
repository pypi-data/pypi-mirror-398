from typing import Optional
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from ..general.models import BaseModel


class CandidatesModel(BaseModel):
    pass


class CandidatesOrganizationModel(CandidatesModel):
    organization: UUID = Field(index=True)


class Document(CandidatesOrganizationModel, table=True):
    type: str = Field(index=True)
    blob_name: str = Field(index=True)

    candidate_id: Optional[UUID] = Field(foreign_key="candidate.id", ondelete="SET NULL", index=True, nullable=True)
    candidate: "Candidate" = Relationship(back_populates="documents")

    application_id: Optional[UUID] = Field(foreign_key="application.id", ondelete="SET NULL", index=False, nullable=True)
    application: "Application" = Relationship(back_populates="documents")


class Candidate(CandidatesOrganizationModel, table=True):
    marksmen_uid: Optional[str] = Field(index=True)

    first_name: str = Field(index=True)
    last_name: str = Field(index=True)
    email: str = Field(index=True)
    phone_number: Optional[str] = Field(index=True)
    city: Optional[str] = Field(index=True)
    country: Optional[str] = Field(index=True)
    documents: list["Document"] = Relationship(back_populates="candidate")
    applications: list["Application"] = Relationship(back_populates="candidate")


class Application(CandidatesOrganizationModel, table=True):
    vacancy_id: UUID = Field(index=True, nullable=True)
    vacancy_title: str = Field(index=True)
    vacancy_reference_number: str = Field(index=True)
    screening_answers: dict = Field(sa_column=Column(JSON))
    status: str = Field(index=True)

    source_id: Optional[UUID] = Field(foreign_key="source.id", ondelete="SET NULL", index=False, nullable=True)
    source: "Source" = Relationship(back_populates="applications")

    candidate_id: Optional[UUID] = Field(foreign_key="candidate.id", ondelete="SET NULL", index=True, nullable=True)
    candidate: Candidate = Relationship(back_populates="applications")

    documents: list["Document"] = Relationship(back_populates="application")


class Source(CandidatesOrganizationModel, table=True):
    source: str = Field(index=True)
    event_id: Optional[str] = Field(index=True)
    campaign_id: Optional[UUID] = Field(index=True)

    applications: list["Application"] = Relationship(back_populates="source")
