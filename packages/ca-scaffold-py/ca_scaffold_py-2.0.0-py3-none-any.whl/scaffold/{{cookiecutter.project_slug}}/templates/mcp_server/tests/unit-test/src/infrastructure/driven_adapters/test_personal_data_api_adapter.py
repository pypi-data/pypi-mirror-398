"""
Unit tests for PersonalDataApiAdapter.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.infrastructure.driven_adapters.api_connect_adapter import (
    PersonalDataApiAdapter,
    ApiConnectError
)
from src.domain.model.personal_data import (
    BasicInformation,
    DetailInformation
)
from src.domain.model.errors.personal_data_error import PersonalDataError


@pytest.fixture
def mock_api_adapter():
    """Create a mock ApiConnectAdapter."""
    return MagicMock()


@pytest.fixture
def config():
    """Create a configuration dictionary."""
    return {
        "basic_information_endpoint": "https://api.test/basic",
        "detail_information_endpoint": "https://api.test/detail"
    }


@pytest.fixture
def personal_data_api_adapter(config, mock_api_adapter):
    """Create a PersonalDataApiAdapter instance with mocked dependencies."""
    return PersonalDataApiAdapter(config, mock_api_adapter)


class TestPersonalDataApiAdapter:
    """Test suite for PersonalDataApiAdapter."""

    @pytest.mark.asyncio
    async def test_get_basic_personal_data_success(
        self,
        personal_data_api_adapter,
        mock_api_adapter
    ):
        """Test successful retrieval of basic personal data."""
        # Arrange
        identification_type = "CC"
        identification_number = "123456789"

        mock_response = {
            "status": 200,
            "body": {
                "data": {
                    "customer": {
                        "uniqueCustomerKey": "key123",
                        "identification": {
                            "type": identification_type,
                            "number": identification_number
                        },
                        "generalInformation": {
                            "firstName": "John",
                            "lastName": "Doe"
                        }
                    }
                }
            }
        }

        mock_api_adapter.make_post_request = AsyncMock(
            return_value=mock_response
        )
        mock_api_adapter.handle_api_error = AsyncMock()

        # Act
        result = await personal_data_api_adapter.get_basic_personal_data(
            identification_type,
            identification_number
        )

        # Assert
        assert isinstance(result, BasicInformation)
        assert result.customer.uniqueCustomerKey == "key123"
        mock_api_adapter.make_post_request.assert_called_once()
        mock_api_adapter.handle_api_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_basic_personal_data_api_error(
        self,
        personal_data_api_adapter,
        mock_api_adapter
    ):
        """Test error handling when API Connect fails."""
        # Arrange
        identification_type = "CC"
        identification_number = "123456789"

        mock_api_adapter.make_post_request = AsyncMock(
            side_effect=ApiConnectError("API connection failed")
        )

        # Act & Assert
        with pytest.raises(PersonalDataError) as exc_info:
            await personal_data_api_adapter.get_basic_personal_data(
                identification_type,
                identification_number
            )

        assert "Failed to get basic personal data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_detailed_personal_data_success(
        self,
        personal_data_api_adapter,
        mock_api_adapter
    ):
        """Test successful retrieval of detailed personal data."""
        # Arrange
        identification_type = "CE"
        identification_number = "987654321"

        mock_response = {
            "status": 200,
            "body": {
                "data": {
                    "customer": {
                        "uniqueCustomerKey": "key456",
                        "identification": {
                            "type": identification_type,
                            "number": identification_number
                        },
                        "naturalPersonInformation": {
                            "firstName": "Jane",
                            "lastName": "Smith"
                        },
                        "detailedInformation": {
                            "address": "123 Main St"
                        }
                    }
                }
            }
        }

        mock_api_adapter.make_post_request = AsyncMock(
            return_value=mock_response
        )
        mock_api_adapter.handle_api_error = AsyncMock()

        # Act
        result = await personal_data_api_adapter.get_detailed_personal_data(
            identification_type,
            identification_number
        )

        # Assert
        assert isinstance(result, DetailInformation)
        assert result.customer.uniqueCustomerKey == "key456"
        mock_api_adapter.make_post_request.assert_called_once()
        mock_api_adapter.handle_api_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_detailed_personal_data_api_error(
        self,
        personal_data_api_adapter,
        mock_api_adapter
    ):
        """Test error handling when API Connect fails for detailed data."""
        # Arrange
        identification_type = "CE"
        identification_number = "987654321"

        mock_api_adapter.make_post_request = AsyncMock(
            side_effect=ApiConnectError("Network timeout")
        )

        # Act & Assert
        with pytest.raises(PersonalDataError) as exc_info:
            await personal_data_api_adapter.get_detailed_personal_data(
                identification_type,
                identification_number
            )

        assert "Failed to get detailed personal data" in str(exc_info.value)

    def test_initialization_with_config(self, config, mock_api_adapter):
        """Test that adapter initializes correctly with config."""
        # Act
        adapter = PersonalDataApiAdapter(config, mock_api_adapter)

        # Assert
        assert adapter.basic_info_endpoint == config[
            "basic_information_endpoint"
        ]
        assert adapter.detail_info_endpoint == config[
            "detail_information_endpoint"
        ]
        assert adapter.api_adapter == mock_api_adapter
