from typing import Optional
from pydantic import AliasChoices, Field, field_validator
from src.applications.settings.base_settings import GeneralBaseSettings
# ANCHOR_SETTINGS_IMPORT (no borrar)


class AwsConfig(GeneralBaseSettings):
    """Class to manage the AWS configuration of the application."""
    aws_access_key_id: Optional[str] = Field(
        default=None,
        alias="AWS_ACCESS_KEY_ID",
        validation_alias=AliasChoices(
            "AWS_ACCESS_KEY_ID", "aws_access_key_id"
        ),
    )

    aws_secret_access_key: Optional[str] = Field(
        default=None,
        alias="AWS_SECRET_ACCESS_KEY",
        validation_alias=AliasChoices(
            "AWS_SECRET_ACCESS_KEY", "aws_secret_access_key"
        ),
    )

    aws_session_token: Optional[str] = Field(
        default=None,
        alias="AWS_SESSION_TOKEN",
        validation_alias=AliasChoices(
            "AWS_SESSION_TOKEN", "aws_session_token"
        ),
    )

    endpoint_url: Optional[str] = Field(
        default=None,
        alias="AWS_ENDPOINT_URL",
        validation_alias=AliasChoices(
            "AWS_ENDPOINT_URL", "aws_endpoint_url", "endpoint_url"
        ),
    )

    region_name: Optional[str] = Field(
        default="us-east-1",
        alias="AWS_REGION",
        validation_alias=AliasChoices(
            "AWS_REGION", "aws_region", "region_name"
        ),
    )


class Config(GeneralBaseSettings):
    """Class to manage the configuration of the application."""
    url_prefix: str = Field(default="/", alias="URL_PREFIX")

    aws: AwsConfig = Field(default_factory=AwsConfig)
    api_secret_name: str = Field(default="", alias="API_SECRET_NAME")

    basic_information_endpoint: str = Field(
        default="",
        alias="BASIC_INFORMATION_ENDPOINT"
    )
    detail_information_endpoint: str = Field(
        default="",
        alias="DETAIL_INFORMATION_ENDPOINT"
    )
    # ANCHOR_SETTINGS_FIELD (no borrar)

    @field_validator("api_secret_name", mode="after")
    @classmethod
    def validate_required_fields(cls, v: str, info) -> str:
        """Validate that required configuration fields are not empty."""
        if not v or v.strip() == "":
            field_name = info.field_name or "UNKNOWN_FIELD"
            raise ValueError(f"{field_name.upper()} cannot be empty")
        return v.strip()

    @field_validator("url_prefix", mode="before")
    @classmethod
    def get_url_prefix(cls, v: str) -> str:
        """Get the URL prefix."""
        if v and not v.startswith("/"):
            v = "/" + v
        v = v.rstrip("/")
        return v

    @field_validator(
        "basic_information_endpoint",
        "detail_information_endpoint",
        # ANCHOR_SETTINGS_VALIDATOR (no borrar)
        mode="after"
    )
    @classmethod
    def validate_endpoints(cls, v: str, info) -> str:
        """Validate that the endpoints are valid URLs."""
        alias = info.field_name or "UNKNOWN_ENDPOINT"

        if not v or v.strip() == "":
            raise ValueError(f"{alias.upper()} cannot be empty")

        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(
                f"{alias.upper()} must be a valid URL (http:// or https://)"
            )

        return v.strip()
