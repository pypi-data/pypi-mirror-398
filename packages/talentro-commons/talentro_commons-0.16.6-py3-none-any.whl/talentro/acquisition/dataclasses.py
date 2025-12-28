from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from talentro.vacancies.dataclasses import VacancyInfo

from ..acquisition.models import ChannelType, CampaignGoal, Campaign as CampaignModel, Ad as AdModel, AdStatus
from ..general.dataclasses import ResolvableCompanyModel
from ..integrations.dataclasses import LinkInfo
from ..services.clients import MSClient
from ..vacancies.dataclasses import FeedInfo


# Campaign object
class CampaignInfo(ResolvableCompanyModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    name: str
    external_id: Optional[str]
    status: str
    last_sync_date: Optional[datetime]
    ad_count: int
    auto_sync: bool
    channel: LinkInfo
    channel_type: ChannelType
    campaign_goal: Optional[CampaignGoal]
    feed: FeedInfo
    selection_criteria: Optional[dict]
    application_flow_settings: Optional[dict]
    status_detail: Optional[str]

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: UUID) -> "CampaignInfo | None":
        result = await MSClient.acquisition().get(f"campaigns/{object_id}/resolve", headers={"X-Organization-ID": str(organization_id)})

        if result.status_code != 200:
            return None

        return CampaignInfo(**result.json())

    @classmethod
    async def from_model(cls: "CampaignInfo", model: CampaignModel) -> 'CampaignInfo':
        channel = await LinkInfo.resolve_object(model.channel_id, model.organization)
        feed = await FeedInfo.resolve_object(model.feed_id, model.organization)

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,
            name=model.name,
            external_id=model.external_id,
            status=model.status,
            last_sync_date=model.last_sync_date,
            ad_count=model.ad_count,
            auto_sync=model.auto_sync,
            channel=channel,
            channel_type=model.channel_type,
            campaign_goal=model.campaign_goal,
            feed=feed,
            selection_criteria=model.selection_criteria,
            application_flow_settings=model.application_flow_settings,
            status_detail=model.status_detail
        )


class CampaignConfig(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    name: str
    external_id: Optional[str]
    status: str
    last_sync_date: Optional[datetime]
    ad_count: int
    auto_sync: bool
    channel_id: UUID
    channel_type: ChannelType
    campaign_goal: Optional[CampaignGoal]
    feed_id: UUID
    selection_criteria: Optional[dict]
    application_flow_settings: Optional[dict]

    @classmethod
    async def from_model(cls: "CampaignConfig", model: CampaignModel) -> 'CampaignConfig':
        return cls(**model.model_dump())


class AdInfo(ResolvableCompanyModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    vacancy: Optional[VacancyInfo]
    campaign: CampaignInfo

    name: str
    external_id: Optional[str]
    status: AdStatus
    primary_text: str
    title: str
    description: Optional[str]
    status_detail: Optional[str]
    conversion_goal: Optional[str]

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: str) -> "ResolvableCompanyModel":
        pass

    @classmethod
    async def from_model(cls: "AdInfo", model: AdModel) -> 'CampaignInfo':
        if model.vacancy_id:
            vacancy = await VacancyInfo.resolve_object(model.vacancy_id, model.organization)
        else:
            vacancy = None

        campaign = await CampaignInfo.from_model(model.campaign)

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,

            name=model.name,
            external_id=model.external_id,
            status=model.status,
            primary_text=model.primary_text,
            title=model.title,
            description=model.description,
            status_detail=model.status_detail,
            conversion_goal=model.conversion_goal,

            vacancy=vacancy,
            campaign=campaign,
        )