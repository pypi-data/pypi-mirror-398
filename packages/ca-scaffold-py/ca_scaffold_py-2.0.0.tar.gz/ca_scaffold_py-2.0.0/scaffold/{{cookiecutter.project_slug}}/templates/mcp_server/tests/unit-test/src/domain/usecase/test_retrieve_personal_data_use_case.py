"""
Unit tests for RetrievePersonalDataUseCase.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.usecase.retrieve_personal_data_use_case import (
    RetrievePersonalDataUseCase
)
from src.domain.model.personal_data import (
    BasicInformation,
    DetailInformation
)
from src.domain.model.errors.personal_data_error import PersonalDataError


@pytest.fixture
def mock_personal_data_adapter():
    """Create a mock PersonalDataAdapter."""
    return MagicMock()


@pytest.fixture
def personal_data_usecase(mock_personal_data_adapter):
    """Create a RetrievePersonalDataUseCase instance with mocked adapter."""
    return RetrievePersonalDataUseCase(mock_personal_data_adapter)


class TestRetrievePersonalDataUseCase:
    """Test suite for RetrievePersonalDataUseCase."""

    @pytest.mark.asyncio
    async def test_get_basic_information_success(
        self,
        personal_data_usecase,
        mock_personal_data_adapter
    ):
        """Test successful retrieval of basic personal information."""
        # Arrange
        identification_type = "CC"
        identification_number = "123456789"
        
        from src.domain.model.personal_data.basic_information_model import (
            Customer
        )
        
        expected_data = BasicInformation(
            customer=Customer(
                uniqueCustomerKey="key123",
                identification={
                    "type": identification_type,
                    "number": identification_number
                },
                generalInformation={
                    "firstName": "John",
                    "lastName": "Doe"
                }
            )
        )
        
        mock_personal_data_adapter.get_basic_personal_data = AsyncMock(
            return_value=expected_data
        )

        # Act
        result = await personal_data_usecase.get_basic_information(
            identification_type,
            identification_number
        )

        # Assert
        assert result == expected_data
        mock_personal_data_adapter.get_basic_personal_data.\
            assert_called_once_with(
                identification_type,
                identification_number
            )

    @pytest.mark.asyncio
    async def test_get_basic_information_error(
        self,
        personal_data_usecase,
        mock_personal_data_adapter
    ):
        """Test error handling when retrieving basic information."""
        # Arrange
        identification_type = "CC"
        identification_number = "123456789"
        
        mock_personal_data_adapter.get_basic_personal_data = AsyncMock(
            side_effect=PersonalDataError("API error")
        )

        # Act & Assert
        with pytest.raises(PersonalDataError):
            await personal_data_usecase.get_basic_information(
                identification_type,
                identification_number
            )

    @pytest.mark.asyncio
    async def test_get_detailed_information_success(
        self,
        personal_data_usecase,
        mock_personal_data_adapter
    ):
        """Test successful retrieval of detailed personal information."""
        # Arrange
        identification_type = "CE"
        identification_number = "987654321"
        
        from src.domain.model.personal_data.detail_information_model import (
            Customer
        )
        
        expected_data = DetailInformation(
            customer=Customer(
                uniqueCustomerKey="key456",
                identification={
                    "type": identification_type,
                    "number": identification_number
                },
                naturalPersonInformation={
                    "firstName": "Jane",
                    "lastName": "Smith"
                },
                detailedInformation={
                    "address": "123 Main St"
                }
            )
        )
        
        mock_personal_data_adapter.get_detailed_personal_data = AsyncMock(
            return_value=expected_data
        )

        # Act
        result = await personal_data_usecase.get_detailed_information(
            identification_type,
            identification_number
        )

        # Assert
        assert result == expected_data
        mock_personal_data_adapter.get_detailed_personal_data.\
            assert_called_once_with(
                identification_type,
                identification_number
            )

    @pytest.mark.asyncio
    async def test_get_detailed_information_error(
        self,
        personal_data_usecase,
        mock_personal_data_adapter
    ):
        """Test error handling when retrieving detailed information."""
        # Arrange
        identification_type = "CE"
        identification_number = "987654321"
        
        mock_personal_data_adapter.get_detailed_personal_data = AsyncMock(
            side_effect=PersonalDataError("Connection error")
        )

        # Act & Assert
        with pytest.raises(PersonalDataError):
            await personal_data_usecase.get_detailed_information(
                identification_type,
                identification_number
            )
