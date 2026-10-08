import pytest
import respx
from httpx import ConnectError, Response

from indexer_price.indexers.financialdata import FinancialDataIndexer

QUOTES_URL = "https://financialdata.net/api/v1/crypto-quotes"
API_KEY = "key-12345678"


def quote_payload(symbol: str = "TONUSD", price: float = 2.34) -> list[dict]:
    """The documented crypto-quotes response shape."""
    return [
        {
            "trading_symbol": symbol,
            "base_asset": symbol.removesuffix("USD"),
            "quote_asset": "USD",
            "time": "2026-10-07 12:00:00",
            "price": price,
            "change": 0.05,
            "percentage_change": 2.18,
        }
    ]


@pytest.mark.asyncio
@respx.mock
async def test_unconfigured_source_is_off_and_never_calls_out() -> None:
    route = respx.get(QUOTES_URL).mock(return_value=Response(200, json=quote_payload()))

    for api_key in (None, ""):
        indexer = FinancialDataIndexer(api_key)
        try:
            assert indexer.enabled is False
            assert await indexer.quote("TONUSD") is None
        finally:
            await indexer.client.aclose()

    assert not route.called


@pytest.mark.asyncio
@respx.mock
async def test_returns_the_price_for_the_pair_asked_for_and_sends_the_key() -> None:
    route = respx.get(QUOTES_URL).mock(
        return_value=Response(
            200, json=quote_payload("BTCUSD", 111394.68) + quote_payload("TONUSD", 2.34)
        )
    )

    indexer = FinancialDataIndexer(API_KEY)
    try:
        assert await indexer.quote("TONUSD") == 2.34
    finally:
        await indexer.client.aclose()

    assert route.called
    params = route.calls[0].request.url.params
    assert params["identifiers"] == "TONUSD"
    assert params["key"] == API_KEY


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        pytest.param([], None, id="pair-not-carried"),
        pytest.param(
            {"message": "Invalid API key"}, None, id="error-object-not-a-list"
        ),
        pytest.param(quote_payload("ETHUSD"), None, id="different-pair-only"),
        pytest.param(
            [{"trading_symbol": "TONUSD", "price": 0}], None, id="zero-is-not-a-price"
        ),
        pytest.param(
            [{"trading_symbol": "TONUSD", "price": "n/a"}], None, id="not-a-number"
        ),
        pytest.param([{"trading_symbol": "TONUSD"}], None, id="no-price-field"),
        pytest.param(
            [None, {"trading_symbol": "TONUSD", "price": 2.5}],
            2.5,
            id="junk-row-skipped",
        ),
    ],
)
async def test_every_unusable_body_is_a_miss_not_an_error(payload, expected) -> None:
    respx.get(QUOTES_URL).mock(return_value=Response(200, json=payload))

    indexer = FinancialDataIndexer(API_KEY)
    try:
        assert await indexer.quote("TONUSD") == expected
    finally:
        await indexer.client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_a_non_200_response_returns_none_and_keeps_the_key_out_of_the_log(
    caplog,
) -> None:
    respx.get(QUOTES_URL).mock(
        return_value=Response(401, json={"message": "Invalid API key"})
    )

    indexer = FinancialDataIndexer(API_KEY)
    try:
        with caplog.at_level("WARNING"):
            assert await indexer.quote("TONUSD") is None
    finally:
        await indexer.client.aclose()

    assert "401" in caplog.text
    assert API_KEY not in caplog.text


@pytest.mark.asyncio
@respx.mock
async def test_a_failed_request_returns_none_instead_of_raising(caplog) -> None:
    respx.get(QUOTES_URL).mock(side_effect=ConnectError("network down"))

    indexer = FinancialDataIndexer(API_KEY)
    try:
        with caplog.at_level("WARNING"):
            assert await indexer.quote("TONUSD") is None
    finally:
        await indexer.client.aclose()

    assert API_KEY not in caplog.text
