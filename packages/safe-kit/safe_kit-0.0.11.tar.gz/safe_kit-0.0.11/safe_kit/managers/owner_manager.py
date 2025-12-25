"""
Owner management functionality for Safe.
"""

from typing import TYPE_CHECKING

from safe_kit.types import SafeTransaction, SafeTransactionData

if TYPE_CHECKING:
    from safe_kit.safe import Safe


class OwnerManagerMixin:
    """
    Mixin class providing owner management functionality.
    """

    def _get_previous_owner(self: "Safe", owner: str) -> str:  # type: ignore[misc]
        """
        Get the previous owner in the linked list for removal/swap operations.
        """
        owners = self.get_owners()
        try:
            index = owners.index(owner)
        except ValueError:
            raise ValueError(f"Address {owner} is not an owner") from None

        if index == 0:
            return "0x0000000000000000000000000000000000000001"  # Sentinel
        return owners[index - 1]

    def create_add_owner_transaction(  # type: ignore[misc]
        self: "Safe", owner: str, threshold: int | None = None
    ) -> SafeTransaction:
        """
        Creates a transaction to add a new owner to the Safe.
        """
        if threshold is None:
            threshold = self.get_threshold()

        data = self.contract.encodeABI(
            fn_name="addOwnerWithThreshold", args=[owner, threshold]
        )

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )

    def create_remove_owner_transaction(  # type: ignore[misc]
        self: "Safe", owner: str, threshold: int | None = None
    ) -> SafeTransaction:
        """
        Creates a transaction to remove an owner from the Safe.
        """
        if threshold is None:
            threshold = self.get_threshold()

        prev_owner = self._get_previous_owner(owner)

        data = self.contract.encodeABI(
            fn_name="removeOwner", args=[prev_owner, owner, threshold]
        )

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )

    def create_swap_owner_transaction(  # type: ignore[misc]
        self: "Safe", old_owner: str, new_owner: str
    ) -> SafeTransaction:
        """
        Creates a transaction to replace an existing owner with a new one.
        """
        prev_owner = self._get_previous_owner(old_owner)

        data = self.contract.encodeABI(
            fn_name="swapOwner", args=[prev_owner, old_owner, new_owner]
        )

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )

    def create_change_threshold_transaction(  # type: ignore[misc]
        self: "Safe", threshold: int
    ) -> SafeTransaction:
        """
        Creates a transaction to change the threshold of the Safe.
        """
        data = self.contract.encodeABI(fn_name="changeThreshold", args=[threshold])

        return self.create_transaction(
            SafeTransactionData(to=self.safe_address, value=0, data=data, operation=0)
        )
