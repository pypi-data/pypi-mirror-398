"""
Module management functionality for Safe.
"""

from typing import TYPE_CHECKING, cast

from safe_kit.types import SafeTransaction, SafeTransactionData

if TYPE_CHECKING:
    from safe_kit.safe import Safe


class ModuleManagerMixin:
    """
    Mixin class providing module management functionality.
    """

    def get_modules(self: "Safe") -> list[str]:  # type: ignore[misc]
        """
        Returns the modules enabled on the Safe.
        """
        # Sentinel address for modules
        start = "0x0000000000000000000000000000000000000001"
        page_size = 10
        modules = []

        while True:
            array, next_module = self.contract.functions.getModulesPaginated(
                start, page_size
            ).call()
            modules.extend(array)

            if (
                next_module == "0x0000000000000000000000000000000000000001"
                or next_module == "0x0000000000000000000000000000000000000000"
            ):
                break
            start = next_module

        return modules

    def is_module_enabled(self: "Safe", module_address: str) -> bool:  # type: ignore[misc]
        """
        Checks if a module is enabled on the Safe.
        """
        return cast(
            bool, self.contract.functions.isModuleEnabled(module_address).call()
        )

    def create_enable_module_transaction(  # type: ignore[misc]
        self: "Safe", module_address: str
    ) -> SafeTransaction:
        """
        Creates a transaction to enable a Safe module.
        """
        data = self.contract.encodeABI(fn_name="enableModule", args=[module_address])

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )

    def create_disable_module_transaction(  # type: ignore[misc]
        self: "Safe", module_address: str
    ) -> SafeTransaction:
        """
        Creates a transaction to disable a Safe module.
        """
        modules = self.get_modules()
        try:
            index = modules.index(module_address)
        except ValueError:
            raise ValueError(f"Module {module_address} is not enabled") from None

        if index == 0:
            prev_module = "0x0000000000000000000000000000000000000001"
        else:
            prev_module = modules[index - 1]

        data = self.contract.encodeABI(
            fn_name="disableModule", args=[prev_module, module_address]
        )

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )
