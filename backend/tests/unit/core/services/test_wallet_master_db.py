from core.services.wallet import WalletService
from tests.factories.wallet import JettonWalletFactory, UserWalletFactory


def test_get_master_wallet_rows_aggregates_jetton_balances(db_session):
    wallet_with_jettons = UserWalletFactory(address="0:" + "a" * 64, balance=100)
    wallet_without_jettons = UserWalletFactory(address="0:" + "b" * 64, balance=None)
    JettonWalletFactory(owner_address=wallet_with_jettons.address, balance=11)
    JettonWalletFactory(owner_address=wallet_with_jettons.address, balance=22)

    rows = WalletService(db_session).get_master_wallet_rows()

    assert rows == [
        {
            "address": wallet_with_jettons.address,
            "user_id": wallet_with_jettons.user_id,
            "ton_balance": 100,
            "jetton_balance_total": 33,
            "jetton_wallets_count": 2,
        },
        {
            "address": wallet_without_jettons.address,
            "user_id": wallet_without_jettons.user_id,
            "ton_balance": None,
            "jetton_balance_total": 0,
            "jetton_wallets_count": 0,
        },
    ]
