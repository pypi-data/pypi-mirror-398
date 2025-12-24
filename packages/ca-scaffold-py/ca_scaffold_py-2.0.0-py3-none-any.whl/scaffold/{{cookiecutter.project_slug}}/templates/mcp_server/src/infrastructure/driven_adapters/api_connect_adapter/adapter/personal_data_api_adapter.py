import logging
from typing import Dict
from src.domain.model.personal_data import BasicInformation, DetailInformation
from src.domain.model.personal_data.gateways.personal_data_adapter import (
    PersonalDataAdapter
)
from src.domain.model.errors.personal_data_error import PersonalDataError
from src.infrastructure.driven_adapters.api_connect_adapter import (
    ApiConnectError,
    ApiConnectAdapter
)


class PersonalDataApiAdapter(PersonalDataAdapter):
    """API Connect adapter for Personal Data operations."""

    def __init__(self,
                 config: Dict,
                 api_adapter: ApiConnectAdapter):
        """
        Initialize Personal Data adapter.

        Args:
            config: Configuration dictionary with API settings
            api_adapter: Shared API Connect adapter instance
        """
        self.basic_info_endpoint = config.get("basic_information_endpoint",
                                              "")
        self.detail_info_endpoint = config.get("detail_information_endpoint",
                                               "")
        self.api_adapter = api_adapter
        self.logger = logging.getLogger(__name__)

    async def get_basic_personal_data(self,
                                      identification_type: str,
                                      identification_number: str
                                      ) -> BasicInformation:
        """Get basic personal data from API Connect."""
        try:
            payload = {
                "data": {
                    "customer": {
                        "identification": {
                            "type": identification_type,
                            "number": identification_number
                        }
                    },
                    "queryType": ""
                }
            }
            result = await self.api_adapter.make_post_request(
                self.basic_info_endpoint,
                payload=payload
            )
            await self.api_adapter.handle_api_error(result)
            return BasicInformation(**result["body"]["data"])
        except ApiConnectError as e:
            self.logger.error(
                "Error fetching basic personal data: %s", str(e)
            )
            raise PersonalDataError(
                "Failed to get basic personal data"
            ) from e

    async def get_detailed_personal_data(
        self,
            identification_type: str,
            identification_number: str
    ) -> DetailInformation:
        """Get detailed personal data from API Connect"""
        additional_headers = {"accept": "application/json"}
        payload = {
            "data": {
                "customer": {
                    "identification": {
                        "type": identification_type,
                        "number": identification_number
                    }
                },
                "queryType": ""
            }
        }
        try:
            result = await self.api_adapter.make_post_request(
                self.detail_info_endpoint,
                payload=payload,
                additional_headers=additional_headers
            )
            await self.api_adapter.handle_api_error(result)
            return DetailInformation(**result["body"]["data"])
        except ApiConnectError as e:
            self.logger.error(
                "Error fetching detailed personal data: %s", str(e)
            )
            raise PersonalDataError(
                "Failed to get detailed personal data"
            ) from e
