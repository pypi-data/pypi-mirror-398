"""
Guard and fallback handler management functionality for Safe.
"""

from typing import TYPE_CHECKING

from safe_kit.types import SafeTransaction, SafeTransactionData

if TYPE_CHECKING:
    from safe_kit.safe import Safe


class GuardManagerMixin:
    """
    Mixin class providing guard and fallback handler management functionality.
    """

    def get_guard(self: "Safe") -> str:  # type: ignore[misc]
        """
        Returns the guard address of the Safe.
        """
        # keccak256("guard_manager.guard.address")
        slot = 0x4A204F620C8C5CCDCA3FD54D003B6D13435454A733A569F8E4A6426EA62BF7A0
        data = self.eth_adapter.get_storage_at(self.safe_address, slot)
        # Convert bytes to address (last 20 bytes)
        return "0x" + data.hex()[-40:]

    def create_set_guard_transaction(  # type: ignore[misc]
        self: "Safe", guard_address: str
    ) -> SafeTransaction:
        """
        Creates a transaction to set the guard of the Safe.
        """
        data = self.contract.encodeABI(fn_name="setGuard", args=[guard_address])

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )

    def get_fallback_handler(self: "Safe") -> str:  # type: ignore[misc]
        """
        Returns the fallback handler address of the Safe.
        """
        # keccak256("fallback_manager.handler.address")
        slot = 0x6C9A6C4A39284E37ED1CF53D337577D14212A4870FB976A4366C693B939918D5
        data = self.eth_adapter.get_storage_at(self.safe_address, slot)
        return "0x" + data.hex()[-40:]

    def create_set_fallback_handler_transaction(  # type: ignore[misc]
        self: "Safe", handler_address: str
    ) -> SafeTransaction:
        """
        Creates a transaction to set the fallback handler of the Safe.
        """
        data = self.contract.encodeABI(
            fn_name="setFallbackHandler", args=[handler_address]
        )

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )
