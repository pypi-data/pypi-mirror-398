from typing import Any, cast

from hexbytes import HexBytes

from safe_kit.adapter import EthAdapter
from safe_kit.contract_types import (
    SafeApproveHashParams,
    SafeExecTransactionParams,
    SafeGetTransactionHashParams,
    SafeIsOwnerParams,
    SafeRequiredTxGasParams,
)
from safe_kit.errors import handle_contract_error
from safe_kit.managers import (
    GuardManagerMixin,
    ModuleManagerMixin,
    OwnerManagerMixin,
    TokenManagerMixin,
)
from safe_kit.types import SafeTransaction, SafeTransactionData

EIP1271_MAGIC_VALUE = "0x1626ba7e"


class Safe(
    OwnerManagerMixin,
    ModuleManagerMixin,
    TokenManagerMixin,
    GuardManagerMixin,
):
    """
    The main class for interacting with a Safe.

    This class provides a comprehensive interface for Safe operations including:
    - Basic Safe info (address, version, balance, nonce, threshold, owners)
    - Transaction creation, signing, and execution
    - Owner management (add, remove, swap owners, change threshold)
    - Module management (enable, disable, list modules)
    - Token transfers (ERC20, ERC721, native ETH)
    - Guard and fallback handler management
    """

    def __init__(
        self, eth_adapter: EthAdapter, safe_address: str, chain_id: int | None = None
    ):
        self.eth_adapter = eth_adapter
        self.safe_address = self.eth_adapter.to_checksum_address(safe_address)

        if not self.eth_adapter.is_contract(self.safe_address):
            raise ValueError(f"Address {self.safe_address} is not a contract")

        self.contract = self.eth_adapter.get_safe_contract(self.safe_address)
        self.chain_id = chain_id

        if self.chain_id is not None:
            adapter_chain_id = self.eth_adapter.get_chain_id()
            if adapter_chain_id != self.chain_id:
                raise ValueError(
                    f"Adapter chain ID ({adapter_chain_id}) does not match "
                    f"Safe chain ID ({self.chain_id})"
                )

    @classmethod
    def create(
        cls, eth_adapter: EthAdapter, safe_address: str, chain_id: int | None = None
    ) -> "Safe":
        """
        Factory method to create a Safe instance.
        """
        return cls(eth_adapter, safe_address, chain_id)

    def get_address(self) -> str:
        """
        Returns the address of the Safe.
        """
        return self.safe_address

    def get_version(self) -> str:
        """
        Returns the version of the Safe contract.
        """
        return cast(str, self.contract.functions.VERSION().call())

    def get_balance(self) -> int:
        """
        Returns the ETH balance of the Safe.
        """
        return self.eth_adapter.get_balance(self.safe_address)

    def get_nonce(self) -> int:
        """
        Returns the current nonce of the Safe.
        """
        return cast(int, self.contract.functions.nonce().call())

    def get_threshold(self) -> int:
        """
        Returns the threshold of the Safe.
        """
        return cast(int, self.contract.functions.getThreshold().call())

    def get_owners(self) -> list[str]:
        """
        Returns the owners of the Safe.
        """
        return cast(list[str], self.contract.functions.getOwners().call())

    def is_owner(self, address: str) -> bool:
        """
        Checks if an address is an owner of the Safe.
        """
        params: SafeIsOwnerParams = {"owner": address}
        return cast(bool, self.contract.functions.isOwner(**params).call())

    def create_transaction(
        self, transaction_data: SafeTransactionData
    ) -> SafeTransaction:
        """
        Creates a Safe transaction ready to be signed.
        """
        if transaction_data.nonce is None:
            transaction_data.nonce = self.get_nonce()

        return SafeTransaction(data=transaction_data)

    def sign_transaction(
        self, safe_transaction: SafeTransaction, method: str = "eth_sign_typed_data"
    ) -> SafeTransaction:
        """
        Signs a Safe transaction with the current signer.
        Supported methods: "eth_sign_typed_data" (EIP-712), "eth_sign" (legacy).
        """
        signer_address = self.eth_adapter.get_signer_address()
        if not signer_address:
            raise ValueError("No signer configured in the adapter")

        chain_id = self.eth_adapter.get_chain_id()

        if method == "eth_sign_typed_data":
            eip712_data = safe_transaction.data.get_eip712_data(
                chain_id, self.safe_address
            )
            signature = self.eth_adapter.sign_typed_data(eip712_data)
        elif method == "eth_sign":
            tx_hash = self.get_transaction_hash(safe_transaction)
            signature = self.eth_adapter.sign_message(tx_hash)
            # Adjust v for eth_sign: v += 4
            # Signature is r(32) + s(32) + v(1)
            # We need to parse it, adjust v, and reconstruct
            sig_bytes = HexBytes(signature)
            r = sig_bytes[:32]
            s = sig_bytes[32:64]
            v = sig_bytes[64]
            v += 4
            signature = (r + s + bytes([v])).hex()
        else:
            raise ValueError(f"Unsupported signing method: {method}")

        safe_transaction.add_signature(signer_address, signature)
        return safe_transaction

    def add_signature(
        self, safe_transaction: SafeTransaction, owner_address: str, signature: str
    ) -> SafeTransaction:
        """
        Adds a signature to a Safe transaction.
        """
        owner_address = self.eth_adapter.to_checksum_address(owner_address)
        safe_transaction.add_signature(owner_address, signature)
        return safe_transaction

    def add_prevalidated_signature(
        self, safe_transaction: SafeTransaction, owner_address: str
    ) -> SafeTransaction:
        """
        Adds a pre-validated signature for a given owner.
        v=1, r=owner, s=0.
        """
        owner_address = self.eth_adapter.to_checksum_address(owner_address)
        # Signature: r(32) + s(32) + v(1)
        # r = owner address, padded to 32 bytes
        # s = 0, padded to 32 bytes
        # v = 1
        r = owner_address.lower().replace("0x", "").zfill(64)
        s = "0" * 64
        v = "01"
        signature = "0x" + r + s + v
        safe_transaction.add_signature(owner_address, signature)
        return safe_transaction

    def get_transaction_hash(self, safe_transaction: SafeTransaction) -> str:
        """
        Returns the hash of the Safe transaction.
        """
        params: SafeGetTransactionHashParams = {
            "to": safe_transaction.data.to,
            "value": safe_transaction.data.value,
            "data": HexBytes(safe_transaction.data.data),
            "operation": safe_transaction.data.operation,
            "safeTxGas": safe_transaction.data.safe_tx_gas,
            "baseGas": safe_transaction.data.base_gas,
            "gasPrice": safe_transaction.data.gas_price,
            "gasToken": safe_transaction.data.gas_token,
            "refundReceiver": safe_transaction.data.refund_receiver,
            "_nonce": (
                safe_transaction.data.nonce
                if safe_transaction.data.nonce is not None
                else 0
            ),
        }

        return cast(
            str,
            self.contract.functions.getTransactionHash(**params).call().hex(),
        )

    def approve_hash(self, hash_to_approve: str) -> str:
        """
        Approves a hash on-chain.
        """
        try:
            params: SafeApproveHashParams = {"hashToApprove": HexBytes(hash_to_approve)}
            tx_hash = self.contract.functions.approveHash(**params).transact(
                {"from": self.eth_adapter.get_signer_address()}
            )
            return cast(str, tx_hash.hex())
        except Exception as e:
            raise handle_contract_error(e) from e

    def execute_transaction(self, safe_transaction: SafeTransaction) -> str:
        """
        Executes a Safe transaction.
        """
        # Sort signatures
        sorted_signatures = safe_transaction.sorted_signatures_bytes

        try:
            params: SafeExecTransactionParams = {
                "to": safe_transaction.data.to,
                "value": safe_transaction.data.value,
                "data": HexBytes(safe_transaction.data.data),
                "operation": safe_transaction.data.operation,
                "safeTxGas": safe_transaction.data.safe_tx_gas,
                "baseGas": safe_transaction.data.base_gas,
                "gasPrice": safe_transaction.data.gas_price,
                "gasToken": safe_transaction.data.gas_token,
                "refundReceiver": safe_transaction.data.refund_receiver,
                "signatures": sorted_signatures,
            }

            tx_hash = self.contract.functions.execTransaction(**params).transact(
                {"from": self.eth_adapter.get_signer_address()}
            )

            return cast(str, tx_hash.hex())
        except Exception as e:
            raise handle_contract_error(e) from e

    def simulate_transaction(self, safe_transaction: SafeTransaction) -> bool:
        """
        Simulates the transaction using eth_call.
        Returns True if the transaction would succeed, False otherwise.
        """
        try:
            params: SafeExecTransactionParams = {
                "to": safe_transaction.data.to,
                "value": safe_transaction.data.value,
                "data": HexBytes(safe_transaction.data.data),
                "operation": safe_transaction.data.operation,
                "safeTxGas": safe_transaction.data.safe_tx_gas,
                "baseGas": safe_transaction.data.base_gas,
                "gasPrice": safe_transaction.data.gas_price,
                "gasToken": safe_transaction.data.gas_token,
                "refundReceiver": safe_transaction.data.refund_receiver,
                "signatures": safe_transaction.sorted_signatures_bytes,
            }

            # Use call() to simulate
            success = self.contract.functions.execTransaction(**params).call(
                {"from": self.eth_adapter.get_signer_address()}
            )

            return cast(bool, success)
        except Exception:
            return False

    def estimate_transaction_gas(self, safe_transaction: SafeTransaction) -> int:
        """
        Estimates the gas required for a Safe transaction.
        """
        params: SafeRequiredTxGasParams = {
            "to": safe_transaction.data.to,
            "value": safe_transaction.data.value,
            "data": HexBytes(safe_transaction.data.data),
            "operation": safe_transaction.data.operation,
            "safeTxGas": safe_transaction.data.safe_tx_gas,
            "baseGas": safe_transaction.data.base_gas,
            "gasPrice": safe_transaction.data.gas_price,
            "gasToken": safe_transaction.data.gas_token,
            "refundReceiver": safe_transaction.data.refund_receiver,
            "signatures": safe_transaction.sorted_signatures_bytes,
        }
        return cast(
            int,
            self.contract.functions.requiredTxGas(**params).call(),
        )

    def check_signatures(self, safe_transaction: SafeTransaction) -> None:
        """
        Checks if the signatures on the transaction are valid.
        Raises an error if signatures are invalid.
        """
        tx_hash = self.get_transaction_hash(safe_transaction)
        # Convert hex string hash to bytes
        tx_hash_bytes = HexBytes(tx_hash)

        self.contract.functions.checkSignatures(
            tx_hash_bytes,
            HexBytes(safe_transaction.data.data),
            safe_transaction.sorted_signatures_bytes,
        ).call()

    def wait_for_transaction(self, tx_hash: str, timeout: int = 120) -> Any:
        """
        Waits for a transaction receipt.
        """
        return self.eth_adapter.wait_for_transaction_receipt(tx_hash, timeout=timeout)

    def get_domain_separator(self) -> str:
        """
        Returns the EIP-712 domain separator of the Safe.
        """
        return cast(str, self.contract.functions.domainSeparator().call().hex())

    def get_message_hash(self, message: str | bytes) -> str:
        """
        Returns the safe message hash for a given message.
        """
        if isinstance(message, str):
            if message.startswith("0x"):
                message_bytes = HexBytes(message)
            else:
                message_bytes = HexBytes(message.encode("utf-8"))
        elif isinstance(message, bytes):
            message_bytes = HexBytes(message)
        else:
            raise TypeError("message must be str or bytes")

        # keccak256(message)
        from eth_hash.auto import keccak

        message_hash = keccak(message_bytes)

        result = self.contract.functions.getMessageHash(message_hash).call().hex()
        if not result.startswith("0x"):
            result = "0x" + result
        return cast(str, result)

    def sign_message(self, message: str | bytes) -> str:
        """
        Signs a message hash using the current signer.
        Returns the signature using eth_sign (EIP-191).
        """
        message_hash = self.get_message_hash(message)
        return self.eth_adapter.sign_message(message_hash)

    def is_valid_signature(
        self, message_hash: str | bytes, signature: str | bytes
    ) -> bool:
        """
        Checks if a signature is valid for a given message hash using EIP-1271.
        """
        if isinstance(message_hash, str):
            message_hash = HexBytes(message_hash)
        if isinstance(signature, str):
            signature = HexBytes(signature)

        try:
            # isValidSignature(bytes32 _data, bytes memory _signature)
            # returns (bytes4)
            result = self.contract.functions.isValidSignature(
                message_hash, signature
            ).call()
            return HexBytes(result) == HexBytes(EIP1271_MAGIC_VALUE)
        except Exception:
            return False
