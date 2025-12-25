from typing import Any, cast

import requests

from safe_kit.errors import SafeServiceError
from safe_kit.types import (
    SafeBalanceResponse,
    SafeCollectibleResponse,
    SafeCreationInfoResponse,
    SafeDataDecoderResponse,
    SafeDelegateResponse,
    SafeIncomingTransactionResponse,
    SafeInfoResponse,
    SafeModuleTransactionResponse,
    SafeMultisigTransactionResponse,
    SafeServiceInfo,
    SafeTokenResponse,
    SafeTransactionData,
)


class SafeServiceClient:
    """
    Client for interacting with the Safe Transaction Service API.
    """

    def __init__(self, service_url: str):
        self.service_url = service_url.rstrip("/")

    def _handle_response(self, response: requests.Response) -> Any:
        try:
            response.raise_for_status()
            if response.content:
                return response.json()
            return None
        except requests.HTTPError as e:
            raise SafeServiceError(f"Service error: {e}", response.status_code) from e
        except Exception as e:
            raise SafeServiceError(f"Unexpected error: {e}") from e

    def get_service_info(self) -> SafeServiceInfo:
        """
        Returns information about the Safe Transaction Service.
        """
        response = requests.get(f"{self.service_url}/v1/about/")
        data = self._handle_response(response)
        return SafeServiceInfo(**data)

    def propose_transaction(
        self,
        safe_address: str,
        safe_tx_data: SafeTransactionData,
        safe_tx_hash: str,
        sender_address: str,
        signature: str,
        origin: str | None = None,
    ) -> None:
        """
        Proposes a transaction to the Safe Transaction Service.
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/multisig-transactions/"

        payload = {
            "to": safe_tx_data.to,
            "value": safe_tx_data.value,
            "data": safe_tx_data.data if safe_tx_data.data else None,
            "operation": safe_tx_data.operation,
            "safeTxGas": safe_tx_data.safe_tx_gas,
            "baseGas": safe_tx_data.base_gas,
            "gasPrice": safe_tx_data.gas_price,
            "gasToken": safe_tx_data.gas_token,
            "refundReceiver": safe_tx_data.refund_receiver,
            "nonce": safe_tx_data.nonce,
            "contractTransactionHash": safe_tx_hash,
            "sender": sender_address,
            "signature": signature,
            "origin": origin,
        }

        response = requests.post(url, json=payload)
        self._handle_response(response)

    def get_pending_transactions(
        self, safe_address: str, current_nonce: int | None = None
    ) -> list[SafeMultisigTransactionResponse]:
        """
        Returns the list of pending transactions for a Safe.
        """
        return self.get_multisig_transactions(
            safe_address,
            executed=False,
            trust=True,
            nonce_gte=current_nonce,
        )

    def get_multisig_transactions(
        self,
        safe_address: str,
        executed: bool | None = None,
        trust: bool | None = None,
        nonce_gte: int | None = None,
        ordering: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SafeMultisigTransactionResponse]:
        """
        Returns the list of multisig transactions for a Safe.
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/multisig-transactions/"
        params: dict[str, Any] = {}

        if executed is not None:
            params["executed"] = str(executed).lower()
        if trust is not None:
            params["trusted"] = str(trust).lower()
        if nonce_gte is not None:
            params["nonce__gte"] = str(nonce_gte)
        if ordering:
            params["ordering"] = ordering
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)

        response = requests.get(url, params=params)
        data = self._handle_response(response)
        results = data.get("results", [])
        return [SafeMultisigTransactionResponse(**tx) for tx in results]

    def confirm_transaction(self, safe_tx_hash: str, signature: str) -> None:
        """
        Adds a confirmation (signature) to a pending transaction.
        """
        url = (
            f"{self.service_url}/v1/multisig-transactions/{safe_tx_hash}/confirmations/"
        )
        payload = {"signature": signature}

        response = requests.post(url, json=payload)
        self._handle_response(response)

    def delete_transaction(self, safe_tx_hash: str, signature: str) -> None:
        """
        Deletes a pending transaction from the Safe Transaction Service.
        Requires the signature of the proposer.
        """
        url = f"{self.service_url}/v1/multisig-transactions/{safe_tx_hash}/"
        payload = {"signature": signature}
        response = requests.delete(url, json=payload)
        self._handle_response(response)

    def get_transaction(self, safe_tx_hash: str) -> SafeMultisigTransactionResponse:
        """
        Returns the details of a specific Safe transaction.
        """
        url = f"{self.service_url}/v1/multisig-transactions/{safe_tx_hash}/"
        response = requests.get(url)
        data = self._handle_response(response)
        return SafeMultisigTransactionResponse(**data)

    def get_safes_by_owner(self, owner_address: str) -> list[str]:
        """
        Returns the list of Safes owned by an address.
        """
        url = f"{self.service_url}/v1/owners/{owner_address}/safes/"
        response = requests.get(url)
        data = self._handle_response(response)
        return cast(list[str], data.get("safes", []))

    def get_balances(
        self, safe_address: str, trusted: bool = False, exclude_spam: bool = True
    ) -> list[SafeBalanceResponse]:
        """
        Returns the balances of a Safe (ETH and ERC20).
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/balances/"
        params = {
            "trusted": str(trusted).lower(),
            "exclude_spam": str(exclude_spam).lower(),
        }
        response = requests.get(url, params=params)
        data = self._handle_response(response)
        return [SafeBalanceResponse(**item) for item in data]

    def get_incoming_transactions(
        self,
        safe_address: str,
        executed: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SafeIncomingTransactionResponse]:
        """
        Returns the incoming transactions (ETH/ERC20) for a Safe.
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/incoming-transfers/"
        params: dict[str, Any] = {}
        if executed is not None:
            params["executed"] = str(executed).lower()
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)

        response = requests.get(url, params=params)
        data = self._handle_response(response)
        results = data.get("results", [])
        return [SafeIncomingTransactionResponse(**tx) for tx in results]

    def get_module_transactions(
        self,
        safe_address: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SafeModuleTransactionResponse]:
        """
        Returns the module transactions for a Safe.
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/module-transactions/"
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)

        response = requests.get(url, params=params)
        data = self._handle_response(response)
        results = data.get("results", [])
        return [SafeModuleTransactionResponse(**tx) for tx in results]

    def get_safe_info(self, safe_address: str) -> SafeInfoResponse:
        """
        Returns detailed information about a Safe.
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/"
        response = requests.get(url)
        data = self._handle_response(response)
        return SafeInfoResponse(**data)

    def get_creation_info(self, safe_address: str) -> SafeCreationInfoResponse:
        """
        Returns information about when and how a Safe was created.
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/creation/"
        response = requests.get(url)
        data = self._handle_response(response)
        return SafeCreationInfoResponse(**data)

    def get_collectibles(
        self,
        safe_address: str,
        trusted: bool = False,
        exclude_spam: bool = True,
    ) -> list[SafeCollectibleResponse]:
        """
        Returns NFTs (ERC721) owned by the Safe.
        """
        url = f"{self.service_url}/v1/safes/{safe_address}/collectibles/"
        params = {
            "trusted": str(trusted).lower(),
            "exclude_spam": str(exclude_spam).lower(),
        }
        response = requests.get(url, params=params)
        data = self._handle_response(response)
        return [SafeCollectibleResponse(**item) for item in data]

    def get_delegates(self, safe_address: str) -> list[SafeDelegateResponse]:
        """
        Returns the list of delegates for a Safe.
        """
        url = f"{self.service_url}/v1/delegates/"
        params = {"safe": safe_address}
        response = requests.get(url, params=params)
        data = self._handle_response(response)
        results = data.get("results", [])
        return [SafeDelegateResponse(**item) for item in results]

    def add_delegate(
        self,
        safe_address: str,
        delegate_address: str,
        delegator: str,
        label: str,
        signature: str,
    ) -> None:
        """
        Adds a delegate to a Safe.
        """
        url = f"{self.service_url}/v1/delegates/"
        payload = {
            "safe": safe_address,
            "delegate": delegate_address,
            "delegator": delegator,
            "label": label,
            "signature": signature,
        }
        response = requests.post(url, json=payload)
        self._handle_response(response)

    def remove_delegate(
        self,
        delegate_address: str,
        delegator: str,
        signature: str,
    ) -> None:
        """
        Removes a delegate.
        """
        url = f"{self.service_url}/v1/delegates/{delegate_address}/"
        payload = {
            "delegator": delegator,
            "signature": signature,
        }
        response = requests.delete(url, json=payload)
        self._handle_response(response)

    def get_tokens(self) -> list[SafeTokenResponse]:
        """
        Returns the list of ERC20 tokens supported by the Safe Transaction Service.
        """
        url = f"{self.service_url}/v1/tokens/"
        response = requests.get(url)
        data = self._handle_response(response)
        results = data.get("results", [])
        return [SafeTokenResponse(**item) for item in results]

    def get_token(self, token_address: str) -> SafeTokenResponse:
        """
        Returns information about a specific token.
        """
        url = f"{self.service_url}/v1/tokens/{token_address}/"
        response = requests.get(url)
        data = self._handle_response(response)
        return SafeTokenResponse(**data)

    def decode_data(self, data: str) -> SafeDataDecoderResponse:
        """
        Decodes transaction data using the Safe Transaction Service.
        """
        url = f"{self.service_url}/v1/data-decoder/"
        payload = {"data": data}
        response = requests.post(url, json=payload)
        data_json = self._handle_response(response)
        return SafeDataDecoderResponse(**data_json)
