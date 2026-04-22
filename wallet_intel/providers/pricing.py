"""Pricing providers with CoinGecko primary and CMC fallback."""
from __future__ import annotations

from wallet_intel.providers.base import HttpProvider


class PricingClient(HttpProvider):
    COINGECKO_URL = "https://pro-api.coingecko.com/api/v3/simple/price"
    CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    def __init__(self, coingecko_api_key: str = "", cmc_api_key: str = ""):
        super().__init__()
        self.coingecko_api_key = coingecko_api_key
        self.cmc_api_key = cmc_api_key

    def get_price(self, coin_id: str, symbol: str | None = None) -> float | None:
        if self.coingecko_api_key:
            try:
                data = self.get(
                    self.COINGECKO_URL,
                    params={"ids": coin_id, "vs_currencies": "usd"},
                    headers={"x-cg-pro-api-key": self.coingecko_api_key},
                )
                price = data.get(coin_id, {}).get("usd")
                if price:
                    return float(price)
            except Exception:  # noqa: BLE001
                pass

        if self.cmc_api_key and symbol:
            data = self.get(
                self.CMC_URL,
                params={"symbol": symbol.upper(), "convert": "USD"},
                headers={"X-CMC_PRO_API_KEY": self.cmc_api_key},
            )
            quote = data.get("data", {}).get(symbol.upper(), {})
            if quote:
                return float(quote[0]["quote"]["USD"]["price"])
        return None
