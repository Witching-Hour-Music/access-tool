from core.settings import CoreSettings


class PriceIndexerSettings(CoreSettings):
    worker_concurrency: int = 5

    getgems_api_key: str | None = None

    # FinancialData.Net: the fallback crypto price source, tried only when the primary
    # upstream fails. Unset = that fallback is off (see indexers/financialdata.py).
    financialdata_api_key: str | None = None


price_indexer_settings = PriceIndexerSettings()
