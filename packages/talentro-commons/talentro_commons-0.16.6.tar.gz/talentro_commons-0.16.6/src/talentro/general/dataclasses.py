from abc import abstractmethod, ABC
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic.dataclasses import dataclass


class SelectionMethod(StrEnum):
    LIST = 'list'
    ALL = 'all'
    RULES = 'rules'

class Operator(StrEnum):
    EQ = 'eq'
    NEQ = 'neq'
    GT = 'gt'
    GTE = 'gte'
    LT = 'lt'
    LTE = 'lte'
    IN = 'in'
    NIN = 'nin'
    REGEX = 'regex'
    LIKE = 'like'
    I_LIKE = 'iLike'
    EXISTS = 'exists'
    NOT_EXISTS = 'notExists'


class ResolvableModel(BaseModel, ABC):

    @staticmethod
    @abstractmethod
    async def resolve_object(object_id: UUID) -> "ResolvableModel":
        pass


class ResolvableCompanyModel(BaseModel, ABC):

    @staticmethod
    @abstractmethod
    async def resolve_object(object_id: UUID, organization_id: str) -> "ResolvableCompanyModel":
        pass


@dataclass
class DropdownOption:
    value: str
    label: str
    detail: str | None = None


@dataclass
class VacancySelectionRule:
    field: str
    operator: Operator
    value: Optional[str] = None


@dataclass
class VacancySelectionCriteria:
    method: SelectionMethod
    rules: Optional[list[VacancySelectionRule]] = None
    selected_ids: Optional[list[UUID]] = None


@dataclass
class FileData:
    file_name: str
    data: str
    content_type: str