from types import SimpleNamespace

import pytest

from core.cli.build_master_wallet_db import _safe_staking_value


class TonApiStub:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error

    async def get_account_nominators_pools(self, address):
        if self.error:
            raise self.error
        return self.payload


@pytest.mark.asyncio
async def test_safe_staking_value_sums_nominators_pool_amounts():
    payload = SimpleNamespace(
        pools=[
            SimpleNamespace(amount="10"),
            {"amount": 15},
            SimpleNamespace(balance=20),
        ]
    )

    value = await _safe_staking_value(TonApiStub(payload), "wallet")

    assert value == 45


@pytest.mark.asyncio
async def test_safe_staking_value_returns_zero_on_lookup_error():
    value = await _safe_staking_value(TonApiStub(error=RuntimeError("boom")), "wallet")

    assert value == 0
