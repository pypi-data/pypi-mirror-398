from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from talentro.acquisition.dataclasses import CampaignInfo
from talentro.vacancies.dataclasses import VacancyInfo
from talentro.candidates.models import Application as ApplicationModel, Document as DocumentModel, Candidate as CandidateModel


class CandidateInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

    @classmethod
    async def from_model(cls: "CandidateInfo", model: CandidateModel) -> 'CandidateInfo':
        return CandidateInfo(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,

            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            phone_number=model.phone_number,
            city=model.city,
            country=model.country,
        )


class ApplicationData(BaseModel):
    status: str
    source: str
    candidate_id: UUID
    vacancy_reference_number: str
    screening_answers: dict


class Application(ApplicationData):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID


class DocumentInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    type: str
    blob_name: str

    @classmethod
    async def from_model(cls: "DocumentInfo", model: DocumentModel) -> 'DocumentInfo':
        return DocumentInfo(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,
            type=model.type,
            blob_name=model.blob_name
        )


class ApplicationInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    status: str
    screening_answers: dict

    vacancy: Optional[VacancyInfo]
    campaign: Optional[CampaignInfo]
    candidate: Optional[CandidateInfo]

    documents: list[DocumentInfo]

    @classmethod
    async def from_model(cls: "ApplicationInfo", model: ApplicationModel) -> 'ApplicationInfo':
        if model.source:
            campaign = await CampaignInfo.resolve_object(model.source.campaign_id, model.organization)
        else:
            campaign = None

        if model.vacancy_id:
            vacancy = await VacancyInfo.resolve_object(model.vacancy_id, model.organization)
        else:
            vacancy = None

        if model.candidate:
            candidate = await CandidateInfo.from_model(model.candidate)
        else:
            candidate = None

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,

            screening_answers=model.screening_answers,
            status=model.status,

            vacancy=vacancy,
            campaign=campaign,
            candidate=candidate,

            documents=[await DocumentInfo.from_model(document) for document in model.documents],
        )
