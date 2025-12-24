import pytest
from fastapi import HTTPException
from src.infrastructure.driven_adapters import ApiConnectAdapter
from src.infrastructure.entry_points.mcp.routes import health_router


@pytest.fixture(name="api_adapter")
def fixture_api_adapter(mocker):
    return mocker.AsyncMock(spec=ApiConnectAdapter)


@pytest.fixture(name="valid_credentials_adapter")
def fixture_valid_credentials_adapter(api_adapter):
    api_adapter.validate_credentials.return_value = True
    return api_adapter


@pytest.fixture(name="invalid_credentials_adapter")
def fixture_invalid_credentials_adapter(api_adapter):
    api_adapter.validate_credentials.return_value = False
    return api_adapter


@pytest.fixture(name="error_adapter")
def fixture_error_adapter(api_adapter):
    api_adapter.validate_credentials.side_effect = (
        AttributeError("Test error")
    )
    return api_adapter


@pytest.mark.asyncio
async def test_health_returns_ok_with_valid_credentials(
    valid_credentials_adapter
):
    result = await health_router.health(valid_credentials_adapter)
    assert result == {"status": "ok", "credentials": "valid"}
    valid_credentials_adapter.validate_credentials.assert_called_once()


@pytest.mark.asyncio
async def test_health_raises_503_with_invalid_credentials(
    invalid_credentials_adapter
):
    with pytest.raises(HTTPException) as exc_info:
        await health_router.health(invalid_credentials_adapter)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == (
        "Service Unavailable: Invalid credentials"
    )
    invalid_credentials_adapter.validate_credentials.assert_called_once()


@pytest.mark.asyncio
async def test_health_raises_503_on_attribute_error(error_adapter):
    with pytest.raises(HTTPException) as exc_info:
        await health_router.health(error_adapter)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Service Unavailable"
    error_adapter.validate_credentials.assert_called_once()


@pytest.mark.asyncio
async def test_health_validates_credentials_called(
    valid_credentials_adapter
):
    await health_router.health(valid_credentials_adapter)
    valid_credentials_adapter.validate_credentials.assert_awaited_once()
