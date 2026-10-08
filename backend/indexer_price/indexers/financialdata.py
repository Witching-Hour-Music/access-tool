import logging

from httpx import AsyncClient, Timeout

from core.constants import REQUEST_TIMEOUT, READ_TIMEOUT, CONNECT_TIMEOUT

timeout = Timeout(REQUEST_TIMEOUT, read=READ_TIMEOUT, connect=CONNECT_TIMEOUT)
logger = logging.getLogger(__name__)


class FinancialDataIndexer:
    """
    Fallback crypto price source: FinancialData.Net (https://financialdata.net).

    `TonPriceIndexer` has a single upstream (diadata.org) and raises on any non-2xx, so a
    diadata outage leaves the cached TON price to go stale -- and TON price is what every
    floor-price threshold in the gating rules is denominated against. This is a second,
    independent source to try before giving up.

    It is off unless ``FINANCIALDATA_API_KEY`` is configured, and it never raises: a caller
    that gets ``None`` is in exactly the position it would have been in without this class.
    Only pairs FinancialData.Net actually carries return a price; for anything else the
    endpoint answers with an empty list, which is a ``None`` here rather than an error.

    Endpoint (per https://financialdata.net/documentation, read 2026-10-07)::

        GET /api/v1/crypto-quotes?identifiers=TONUSD&key=...
        -> [{"trading_symbol": "TONUSD", "base_asset": "TON", "quote_asset": "USD",
             "time": "2026-10-07 12:00:00", "price": 2.34, "change": 0.05,
             "percentage_change": 2.18}]

    The key is a query parameter, so it is never logged: failures are reported with the
    status code and the pair, never the URL.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self.client = AsyncClient(base_url="https://financialdata.net", timeout=timeout)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def quote(self, trading_symbol: str) -> float | None:
        """
        Fetch the latest USD price for a crypto pair, or ``None`` when this source is
        unconfigured, does not carry the pair, or is unreachable.

        :param trading_symbol: the pair, e.g. ``TONUSD``.
        :return: the price, or ``None``. Never raises.
        """
        if not self.enabled:
            return None

        try:
            response = await self.client.get(
                "/api/v1/crypto-quotes",
                params={"identifiers": trading_symbol, "key": self.api_key},
            )
        except Exception as exc:  # noqa: BLE001 -- a fallback must not raise
            logger.warning(
                "FinancialData.Net request for %s failed: %s",
                trading_symbol,
                type(exc).__name__,
            )
            return None

        if response.status_code != 200:
            # The status only. The URL carries the key, so it never reaches the log.
            logger.warning(
                "FinancialData.Net returned HTTP %s for %s",
                response.status_code,
                trading_symbol,
            )
            return None

        try:
            rows = response.json()
        except ValueError:
            logger.warning(
                "FinancialData.Net returned a non-JSON body for %s", trading_symbol
            )
            return None

        if not isinstance(rows, list):
            # An error body is an object, e.g. {"message": "Invalid API key"}.
            logger.warning(
                "FinancialData.Net did not return quotes for %s", trading_symbol
            )
            return None

        for row in rows:
            if not isinstance(row, dict):
                continue
            symbol = row.get("trading_symbol")
            if not isinstance(symbol, str) or symbol.upper() != trading_symbol.upper():
                continue
            try:
                price = float(row["price"])
            except (KeyError, TypeError, ValueError):
                break
            if price > 0:
                logger.info("FinancialData.Net price for %s: %s", trading_symbol, price)
                return price
            break

        logger.warning("FinancialData.Net has no usable %s quote", trading_symbol)
        return None
