from abc import ABC, abstractmethod
from typing import Any

from eth_account.signers.local import LocalAccount
from web3 import Web3


class EthAdapter(ABC):
    """
    Abstract base class for Ethereum adapters.
    """

    @abstractmethod
    def get_balance(self, address: str) -> int:
        pass

    @abstractmethod
    def get_chain_id(self) -> int:
        pass

    @abstractmethod
    def get_safe_contract(self, safe_address: str) -> Any:
        pass

    @abstractmethod
    def get_contract(self, address: str, abi: list[Any]) -> Any:
        pass

    @abstractmethod
    def get_signer_address(self) -> str | None:
        pass

    @abstractmethod
    def sign_message(self, message: str) -> str:
        pass

    @abstractmethod
    def sign_typed_data(self, data: dict[str, Any]) -> str:
        pass

    @abstractmethod
    def get_storage_at(self, address: str, position: int) -> bytes:
        pass

    @abstractmethod
    def get_code(self, address: str) -> bytes:
        pass

    @abstractmethod
    def get_transaction_count(self, address: str) -> int:
        pass

    @abstractmethod
    def is_contract(self, address: str) -> bool:
        pass

    @abstractmethod
    def to_checksum_address(self, address: str) -> str:
        pass

    @abstractmethod
    def wait_for_transaction_receipt(self, tx_hash: str, timeout: int = 120) -> Any:
        pass


class Web3Adapter(EthAdapter):
    """
    Web3.py implementation of the EthAdapter.
    """

    def __init__(self, web3: Web3, signer: LocalAccount | None = None):
        self.web3 = web3
        self.signer = signer

    def get_balance(self, address: str) -> int:
        return self.web3.eth.get_balance(self.web3.to_checksum_address(address))

    def get_chain_id(self) -> int:
        return self.web3.eth.chain_id

    def get_safe_contract(self, safe_address: str) -> Any:
        from safe_kit.abis import SAFE_ABI

        return self.web3.eth.contract(
            address=self.web3.to_checksum_address(safe_address), abi=SAFE_ABI
        )

    def get_contract(self, address: str, abi: list[Any]) -> Any:
        return self.web3.eth.contract(
            address=self.web3.to_checksum_address(address), abi=abi
        )

    def get_signer_address(self) -> str | None:
        if self.signer:
            return str(self.signer.address)
        return None

    def sign_message(self, message: str) -> str:
        if not self.signer:
            raise ValueError("No signer available")

        from eth_account.messages import encode_defunct

        # Check if message is a hex string (likely a hash)
        if message.startswith("0x"):
            signable_message = encode_defunct(hexstr=message)
        else:
            signable_message = encode_defunct(text=message)

        signed_message = self.signer.sign_message(signable_message)  # type: ignore[no-untyped-call]
        return str(signed_message.signature.hex())

    def sign_typed_data(self, data: dict[str, Any]) -> str:
        if not self.signer:
            raise ValueError("No signer available")
        from eth_account.messages import encode_typed_data

        signable_message = encode_typed_data(full_message=data)
        signed_message = self.signer.sign_message(signable_message)  # type: ignore[no-untyped-call]
        return str(signed_message.signature.hex())

    def get_storage_at(self, address: str, position: int) -> bytes:
        return self.web3.eth.get_storage_at(
            self.web3.to_checksum_address(address), position
        )

    def get_code(self, address: str) -> bytes:
        return self.web3.eth.get_code(self.web3.to_checksum_address(address))

    def get_transaction_count(self, address: str) -> int:
        return self.web3.eth.get_transaction_count(
            self.web3.to_checksum_address(address)
        )

    def is_contract(self, address: str) -> bool:
        code = self.get_code(address)
        return len(code) > 0

    def to_checksum_address(self, address: str) -> str:
        return self.web3.to_checksum_address(address)

    def wait_for_transaction_receipt(self, tx_hash: str, timeout: int = 120) -> Any:
        from hexbytes import HexBytes

        return self.web3.eth.wait_for_transaction_receipt(
            HexBytes(tx_hash), timeout=timeout
        )
