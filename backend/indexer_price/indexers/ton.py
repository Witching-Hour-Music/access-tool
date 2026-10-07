import logging

from httpx import AsyncClient, HTTPError, Timeout
from pydantic import ValidationError

from core.constants import REQUEST_TIMEOUT, READ_TIMEOUT, CONNECT_TIMEOUT
from core.services.ton import TonPriceManager
from indexer_price.dtos.ton import TonPrice
from indexer_price.indexers.financialdata import FinancialDataIndexer
from indexer_price.settings import price_indexer_settings

timeout = Timeout(REQUEST_TIMEOUT, read=READ_TIMEOUT, connect=CONNECT_TIMEOUT)
logger = logging.getLogger(__name__)


TON_FALLBACK_TRADING_SYMBOL = "TONUSD"


class TonPriceIndexer:
    def __init__(self, fallback: FinancialDataIndexer | None = None) -> None:
        self.client = AsyncClient(base_url="https://api.diadata.org", timeout=timeout)
        self.price_manager = TonPriceManager()
        # Off unless FINANCIALDATA_API_KEY is configured; see indexers/financialdata.py.
        self.fallback = fallback or FinancialDataIndexer(
            price_indexer_settings.financialdata_api_key
        )

    async def index(self) -> float:
        """
        Fetches the latest price for the TON asset and sets the fetched price.

        Asks DIAdata first. If that request fails or does not validate, and a fallback
        source is configured, the fallback is asked before the error is raised: TON price is
        what every floor-price threshold is denominated against, so a single upstream having
        a bad minute should not leave the cached price to go stale. With no fallback
        configured the behaviour is unchanged -- the original error propagates.

        :raises HTTPError: If the request fails and no fallback price is available.
        :raises ValidationError: If the response cannot be validated against the TonPrice
            model and no fallback price is available.

        :return: The latest price of the TON asset.
        :rtype: float
        """
        try:
            response = await self.client.get(
                "/v1/assetQuotation/Ton/0x0000000000000000000000000000000000000000"
            )
            response.raise_for_status()
            price = TonPrice.model_validate(response.json()).price
        except (HTTPError, ValidationError, ValueError):
            # Only an upstream problem falls through: a bug in here must still surface.
            if not self.fallback.enabled:
                raise
            logger.warning(
                "DIAdata TON price lookup failed; trying the fallback source"
            )
            price = await self.fallback.quote(TON_FALLBACK_TRADING_SYMBOL)
            if price is None:
                raise

        logger.info(f"Got new price for TON: {price}")
        self.price_manager.set_ton_price(price)
        return price
