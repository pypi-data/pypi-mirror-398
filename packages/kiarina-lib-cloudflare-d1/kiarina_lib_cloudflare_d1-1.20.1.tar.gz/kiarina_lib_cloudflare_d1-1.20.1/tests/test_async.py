import pytest

from kiarina.lib.cloudflare.d1.asyncio import create_d1_client


async def test_success(load_settings) -> None:
    client = create_d1_client()
    result = await client.query("SELECT 1")
    assert result.success
    assert len(result.first.rows) == 1


async def test_error(load_settings) -> None:
    client = create_d1_client()

    result = await client.query("SELECT * FROM non_existent_table")
    assert not result.success
    assert len(result.errors) > 0

    with pytest.raises(ValueError, match="No results available"):
        result.first

    with pytest.raises(RuntimeError, match="Query failed:"):
        result.raise_for_status()
