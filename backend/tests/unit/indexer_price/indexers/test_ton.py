import pytest
import respx
from httpx import ConnectError, Response

from indexer_price.indexers.financialdata import FinancialDataIndexer
from indexer_price.indexers.ton import TonPriceIndexer

DIADATA_URL = (
    "https://api.diadata.org/v1/assetQuotation/Ton/"
    "0x0000000000000000000000000000000000000000"
)
QUOTES_URL = "https://financialdata.net/api/v1/crypto-quotes"
API_KEY = "key-12345678"


def ton_quotation(price: float = 2.0) -> dict:
    return {"Symbol": "TON", "Name": "Toncoin", "Price": price}


class RecordingPriceManager:
    """Stands in for TonPriceManager, which writes the price to Redis."""

    def __init__(self) -> None:
        self.prices: list[float] = []

    def set_ton_price(self, price: float) -> None:
        self.prices.append(price)


def make_indexer(api_key: str | None) -> tuple[TonPriceIndexer, RecordingPriceManager]:
    indexer = TonPriceIndexer(FinancialDataIndexer(api_key))
    manager = RecordingPriceManager()
    indexer.price_manager = manager  # type: ignore[assignment]
    return indexer, manager


async def close(indexer: TonPriceIndexer) -> None:
    await indexer.client.aclose()
    await indexer.fallback.client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_diadata_is_preferred_and_the_fallback_is_never_asked() -> None:
    respx.get(DIADATA_URL).mock(return_value=Response(200, json=ton_quotation(2.0)))
    fallback_route = respx.get(QUOTES_URL)

    indexer, manager = make_indexer(API_KEY)
    try:
        assert await indexer.index() == 2.0
    finally:
        await close(indexer)

    assert manager.prices == [2.0]
    assert not fallback_route.called


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize(
    "diadata",
    [
        pytest.param(
            {"side_effect": ConnectError("network down")}, id="request-failed"
        ),
        pytest.param({"return_value": Response(503)}, id="http-503"),
        pytest.param(
            {"return_value": Response(200, json={"nope": 1})}, id="unvalidatable-body"
        ),
    ],
)
async def test_the_fallback_supplies_the_price_when_diadata_cannot(diadata) -> None:
    respx.get(DIADATA_URL).mock(**diadata)
    respx.get(QUOTES_URL).mock(
        return_value=Response(200, json=[{"trading_symbol": "TONUSD", "price": 2.34}])
    )

    indexer, manager = make_indexer(API_KEY)
    try:
        assert await indexer.index() == 2.34
    finally:
        await close(indexer)

    assert manager.prices == [2.34]


@pytest.mark.asyncio
@respx.mock
async def test_no_fallback_configured_still_propagates_the_error() -> None:
    respx.get(DIADATA_URL).mock(return_value=Response(503))
    fallback_route = respx.get(QUOTES_URL)

    indexer, manager = make_indexer(None)
    try:
        with pytest.raises(Exception):
            await indexer.index()
    finally:
        await close(indexer)

    assert manager.prices == [], "no price is set when the lookup fails"
    assert not fallback_route.called


@pytest.mark.asyncio
@respx.mock
async def test_a_fallback_with_no_quote_either_re_raises_the_original_error() -> None:
    respx.get(DIADATA_URL).mock(return_value=Response(503))
    respx.get(QUOTES_URL).mock(return_value=Response(200, json=[]))

    indexer, manager = make_indexer(API_KEY)
    try:
        with pytest.raises(Exception):
            await indexer.index()
    finally:
        await close(indexer)

    assert manager.prices == []
