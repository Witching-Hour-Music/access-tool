import pytest
from sqlalchemy.orm import Session

from core.services.wallet import WalletService
from tests.factories.jetton import JettonFactory
from tests.factories.wallet import JettonWalletFactory, UserWalletFactory


@pytest.mark.usefixtures("db_session")
def test_get_master_wallet_rows_aggregates_balances(db_session: Session):
    wallet = UserWalletFactory.with_session(db_session).create(balance=1000)
    other_wallet = UserWalletFactory.with_session(db_session).create(balance=700)

    jetton = JettonFactory.with_session(db_session).create()

    JettonWalletFactory.with_session(db_session).create(
        owner_address=wallet.address,
        jetton=jetton,
        balance=300,
    )
    JettonWalletFactory.with_session(db_session).create(
        owner_address=wallet.address,
        jetton=jetton,
        balance=500,
    )

    service = WalletService(db_session)
    rows = service.get_master_wallet_rows()

    by_address = {row["wallet_address"]: row for row in rows}

    assert by_address[wallet.address]["ton_balance"] == 1000
    assert by_address[wallet.address]["jetton_balance_total"] == 800
    assert by_address[wallet.address]["jetton_wallets_count"] == 2

    assert by_address[other_wallet.address]["ton_balance"] == 700
    assert by_address[other_wallet.address]["jetton_balance_total"] == 0
    assert by_address[other_wallet.address]["jetton_wallets_count"] == 0
