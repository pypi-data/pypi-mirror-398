from abc import ABC, abstractmethod
from src.domain.model.personal_data import BasicInformation, DetailInformation


class PersonalDataAdapter(ABC):
    """Domain adapter for managing personal data."""

    @abstractmethod
    async def get_basic_personal_data(
        self,
        identification_type: str,
        identification_number: str
    ) -> BasicInformation:
        """Gets basic information of a person."""

    @abstractmethod
    async def get_detailed_personal_data(
            self,
            identification_type: str,
            identification_number: str
    ) -> DetailInformation:
        """Gets detailed information of a person."""
