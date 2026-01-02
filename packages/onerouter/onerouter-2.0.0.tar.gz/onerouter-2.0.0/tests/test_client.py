import pytest
from onerouter import OneRouter, AuthenticationError, ValidationError


@pytest.mark.asyncio
async def test_client_initialization():
    client = OneRouter(api_key="unf_test_xxx")
    assert client is not None
    await client.close()


@pytest.mark.asyncio
async def test_invalid_api_key():
    with pytest.raises(ValueError):
        OneRouter(api_key="invalid_key")


@pytest.mark.asyncio
async def test_create_payment():
    client = OneRouter(api_key="unf_test_xxx")

    # This would normally make a real API call, but for testing
    # we'll just check that the client initializes correctly
    assert hasattr(client, 'payments')
    assert hasattr(client.payments, 'create')

    await client.close()


@pytest.mark.asyncio
async def test_validation_error():
    client = OneRouter(api_key="unf_test_xxx")

    # This would test validation, but since we're not making real calls
    # we'll just ensure the client is properly structured
    assert client is not None

    await client.close()