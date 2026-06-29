from types import SimpleNamespace

import pytest

from core.cli.build_master_wallet_db import _extract_staking_amount, _safe_staking_value


class PoolObject:
    def __init__(self, amount):
        self.amount = amount


def test_extract_staking_amount_sums_account_staking_pools():
    staking_info = SimpleNamespace(
        pools=[
            SimpleNamespace(amount=100, pending_deposit=900),
            SimpleNamespace(amount="250", pending_withdraw=50),
            {"amount": 50, "ready_withdraw": 10},
        ]
    )

    assert _extract_staking_amount(staking_info) == 400


def test_extract_staking_amount_supports_legacy_shapes():
    assert _extract_staking_amount({"staked": "123"}) == 123
    assert _extract_staking_amount(SimpleNamespace(total="456")) == 456
    assert _extract_staking_amount(None) == 0


@pytest.mark.asyncio
async def test_safe_staking_value_uses_staking_endpoint():
    class TonApi:
        async def get_account_staking(self, address):
            assert address == "wallet-address"
            return {"pools": [{"amount": 100}, {"amount": "200"}]}

    assert await _safe_staking_value("wallet-address", TonApi()) == 300


@pytest.mark.asyncio
async def test_safe_staking_value_falls_back_to_account_info_staking():
    class TonApi:
        async def get_account_staking(self, address):
            raise AttributeError

        async def get_account_info(self, address):
            assert address == "wallet-address"
            return SimpleNamespace(staking=SimpleNamespace(pools=[PoolObject("700")]))

    assert await _safe_staking_value("wallet-address", TonApi()) == 700
