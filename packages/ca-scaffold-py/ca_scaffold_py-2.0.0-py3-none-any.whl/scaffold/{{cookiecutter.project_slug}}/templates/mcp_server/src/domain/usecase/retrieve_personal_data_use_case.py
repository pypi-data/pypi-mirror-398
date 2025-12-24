from src.domain.model.personal_data import (
    BasicInformation,
    DetailInformation
)
from src.domain.model.personal_data.gateways.personal_data_adapter import (
    PersonalDataAdapter
)


class RetrievePersonalDataUseCase:
    """Use case for retrieving personal data information."""

    def __init__(self, personal_data_adapter: PersonalDataAdapter):
        """
        Initialize with a personal data adapter dependency.

        Args:
            personal_data_adapter: Adapter for personal data operations
        """
        self.personal_data_adapter = personal_data_adapter

    async def get_basic_information(
        self,
        identification_type: str,
        identification_number: str
    ) -> BasicInformation:
        """
        Get basic personal information.

        Args:
            identification_type: Type of identification (e.g., 'CC', 'CE')
            identification_number: Identification number

        Returns:
            BasicInformation: Basic personal information

        Raises:
            PersonalDataError: If data retrieval fails
        """
        return await self.personal_data_adapter.get_basic_personal_data(
            identification_type,
            identification_number
        )

    async def get_detailed_information(
        self,
        identification_type: str,
        identification_number: str
    ) -> DetailInformation:
        """
        Get detailed personal information.

        Args:
            identification_type: Type of identification (e.g., 'CC', 'CE')
            identification_number: Identification number

        Returns:
            DetailInformation: Detailed personal information

        Raises:
            PersonalDataError: If data retrieval fails
        """
        return await self.personal_data_adapter.get_detailed_personal_data(
            identification_type,
            identification_number
        )
