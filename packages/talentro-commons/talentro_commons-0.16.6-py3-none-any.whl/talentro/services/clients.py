import os

from httpx import AsyncClient

from talentro.util.singleton import SingletonMeta


class MSClient(metaclass=SingletonMeta):

    _integrations_client: AsyncClient | None = None
    _acquisition_client: AsyncClient | None = None
    _vacancies_client: AsyncClient | None = None
    _candidates_client: AsyncClient | None = None

    @classmethod
    def integrations(cls) -> AsyncClient:
        if cls._integrations_client is None:
            cls._integrations_client = AsyncClient(
                base_url=f"{os.getenv('INTEGRATIONS_BASE_URL')}/api/v1/",
                timeout=30,
            )
        return cls._integrations_client

    @classmethod
    def acquisition(cls) -> AsyncClient:
        if cls._acquisition_client is None:
            cls._acquisition_client = AsyncClient(
                base_url=f"{os.getenv('ACQUISITION_BASE_URL')}/api/v1/",
                timeout=30,
            )
        return cls._acquisition_client

    @classmethod
    def vacancies(cls) -> AsyncClient:
        if cls._vacancies_client is None:
            cls._vacancies_client = AsyncClient(
                base_url=f"{os.getenv('VACANCIES_BASE_URL')}/api/v1/",
                timeout=30,
            )
        return cls._vacancies_client

    @classmethod
    def candidates(cls) -> AsyncClient:
        if cls._candidates_client is None:
            cls._candidates_client = AsyncClient(
                base_url=f"{os.getenv('CANDIDATES_BASE_URL')}/api/v1/",
                timeout=30,
            )
        return cls._candidates_client

    @classmethod
    async def aclose(cls) -> None:
        if cls._integrations_client is not None:
            await cls._integrations_client.aclose()
            cls._integrations_client = None
        if cls._acquisition_client is not None:
            await cls._acquisition_client.aclose()
            cls._acquisition_client = None
        if cls._vacancies_client is not None:
            await cls._vacancies_client.aclose()
            cls._vacancies_client = None
        if cls._candidates_client is not None:
            await cls._candidates_client.aclose()
            cls._candidates_client = None
