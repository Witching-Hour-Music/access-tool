"""EVM address validation utilities."""
from web3 import Web3


def normalize_evm(address: str) -> str:
    return Web3.to_checksum_address(address)


def validate_evm(address: str) -> tuple[bool, str | None, str | None]:
    try:
        checksum = normalize_evm(address)
        return True, checksum, None
    except Exception as exc:  # noqa: BLE001
        return False, None, str(exc)
