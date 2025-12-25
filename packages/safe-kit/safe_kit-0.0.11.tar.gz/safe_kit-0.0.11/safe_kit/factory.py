from typing import cast

from hexbytes import HexBytes

from safe_kit.abis import SAFE_PROXY_FACTORY_ABI
from safe_kit.adapter import EthAdapter
from safe_kit.contract_types import (
    SafeProxyFactoryCreateChainSpecificProxyWithNonceParams,
    SafeProxyFactoryCreateProxyWithNonceParams,
)
from safe_kit.errors import handle_contract_error
from safe_kit.safe import Safe
from safe_kit.types import SafeAccountConfig


class SafeFactory:
    """
    Factory class to deploy new Safe contracts.
    """

    def __init__(
        self,
        eth_adapter: EthAdapter,
        safe_singleton_address: str,
        safe_proxy_factory_address: str,
    ):
        self.eth_adapter = eth_adapter
        self.safe_singleton_address = safe_singleton_address
        self.safe_proxy_factory_address = safe_proxy_factory_address
        self.proxy_factory_contract = self.eth_adapter.get_contract(
            address=safe_proxy_factory_address, abi=SAFE_PROXY_FACTORY_ABI
        )

    def _get_initializer_data(self, config: SafeAccountConfig) -> bytes:
        safe_singleton = self.eth_adapter.get_safe_contract(self.safe_singleton_address)
        return cast(
            bytes,
            safe_singleton.encodeABI(
                fn_name="setup",
                args=[
                    config.owners,
                    config.threshold,
                    config.to,
                    HexBytes(config.data),
                    config.fallback_handler,
                    config.payment_token,
                    config.payment,
                    config.payment_receiver,
                ],
            ),
        )

    def predict_safe_address(
        self, config: SafeAccountConfig, salt_nonce: int = 0
    ) -> str:
        """
        Predicts the address of the Safe that would be deployed with the given
        configuration.
        """
        initializer = self._get_initializer_data(config)
        params: SafeProxyFactoryCreateProxyWithNonceParams = {
            "_singleton": self.safe_singleton_address,
            "initializer": initializer,
            "saltNonce": salt_nonce,
        }
        return cast(
            str,
            self.proxy_factory_contract.functions.createProxyWithNonce(**params).call(),
        )

    def predict_safe_address_v1_4_1(
        self, config: SafeAccountConfig, salt_nonce: int = 0
    ) -> str:
        """
        Predicts the address of the Safe (v1.4.1) that would be deployed.
        Uses createChainSpecificProxyWithNonce.
        """
        initializer = self._get_initializer_data(config)
        params: SafeProxyFactoryCreateChainSpecificProxyWithNonceParams = {
            "_singleton": self.safe_singleton_address,
            "initializer": initializer,
            "saltNonce": salt_nonce,
        }
        return cast(
            str,
            self.proxy_factory_contract.functions.createChainSpecificProxyWithNonce(
                **params
            ).call(),
        )

    def deploy_safe(self, config: SafeAccountConfig, salt_nonce: int = 0) -> Safe:
        """
        Deploys a new Safe contract.
        Returns a Safe instance with the predicted address.
        """
        signer = self.eth_adapter.get_signer_address()
        if not signer:
            raise ValueError("No signer configured in the adapter")

        initializer = self._get_initializer_data(config)
        safe_address = self.predict_safe_address(config, salt_nonce)

        try:
            params: SafeProxyFactoryCreateProxyWithNonceParams = {
                "_singleton": self.safe_singleton_address,
                "initializer": initializer,
                "saltNonce": salt_nonce,
            }
            self.proxy_factory_contract.functions.createProxyWithNonce(
                **params
            ).transact({"from": signer})
        except Exception as e:
            raise handle_contract_error(e) from e

        return Safe(self.eth_adapter, safe_address)

    def deploy_safe_v1_4_1(
        self, config: SafeAccountConfig, salt_nonce: int = 0
    ) -> Safe:
        """
        Deploys a new Safe contract (v1.4.1).
        Returns a Safe instance with the predicted address.
        """
        signer = self.eth_adapter.get_signer_address()
        if not signer:
            raise ValueError("No signer configured in the adapter")

        initializer = self._get_initializer_data(config)
        safe_address = self.predict_safe_address_v1_4_1(config, salt_nonce)

        try:
            params: SafeProxyFactoryCreateChainSpecificProxyWithNonceParams = {
                "_singleton": self.safe_singleton_address,
                "initializer": initializer,
                "saltNonce": salt_nonce,
            }
            self.proxy_factory_contract.functions.createChainSpecificProxyWithNonce(
                **params
            ).transact({"from": signer})
        except Exception as e:
            raise handle_contract_error(e) from e

        return Safe(self.eth_adapter, safe_address)
