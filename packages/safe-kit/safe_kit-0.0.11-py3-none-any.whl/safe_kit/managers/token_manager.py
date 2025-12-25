"""
Token transfer functionality for Safe.
"""

from typing import TYPE_CHECKING

from safe_kit.types import SafeTransaction, SafeTransactionData

if TYPE_CHECKING:
    from safe_kit.safe import Safe


class TokenManagerMixin:
    """
    Mixin class providing token transfer functionality.
    """

    def create_erc20_transfer_transaction(  # type: ignore[misc]
        self: "Safe", token_address: str, to: str, amount: int
    ) -> SafeTransaction:
        """
        Creates a transaction to transfer ERC20 tokens.
        """
        from safe_kit.abis import ERC20_ABI

        token_contract = self.eth_adapter.get_contract(token_address, ERC20_ABI)

        data = token_contract.encodeABI(fn_name="transfer", args=[to, amount])

        return self.create_transaction(
            SafeTransactionData(to=token_address, value=0, data=data, operation=0)
        )

    def create_erc721_transfer_transaction(  # type: ignore[misc]
        self: "Safe", token_address: str, to: str, token_id: int
    ) -> SafeTransaction:
        """
        Creates a transaction to transfer ERC721 tokens.
        """
        from safe_kit.abis import ERC721_ABI

        token_contract = self.eth_adapter.get_contract(token_address, ERC721_ABI)

        data = token_contract.encodeABI(
            fn_name="safeTransferFrom", args=[self.safe_address, to, token_id]
        )

        return self.create_transaction(
            SafeTransactionData(to=token_address, value=0, data=data, operation=0)
        )

    def create_native_transfer_transaction(  # type: ignore[misc]
        self: "Safe", to: str, amount: int
    ) -> SafeTransaction:
        """
        Creates a transaction to transfer native tokens (ETH).
        """
        return self.create_transaction(
            SafeTransactionData(to=to, value=amount, data="0x", operation=0)
        )

    def create_rejection_transaction(self: "Safe", nonce: int) -> SafeTransaction:  # type: ignore[misc]
        """
        Creates a transaction to reject a pending transaction (by reusing the nonce).
        """
        return self.create_transaction(
            SafeTransactionData(
                to=self.safe_address, value=0, data="0x", operation=0, nonce=nonce
            )
        )

    def create_multi_send_transaction(  # type: ignore[misc]
        self: "Safe",
        transactions: list[SafeTransactionData],
        multi_send_address: str,
    ) -> SafeTransaction:
        """
        Creates a MultiSend transaction.
        """
        from safe_kit.abis import MULTI_SEND_ABI
        from safe_kit.multisend import MultiSend

        encoded_txs = MultiSend.encode_transactions(transactions)

        multi_send_contract = self.eth_adapter.get_contract(
            multi_send_address, MULTI_SEND_ABI
        )

        data = multi_send_contract.encodeABI(fn_name="multiSend", args=[encoded_txs])

        # MultiSend transactions are DelegateCalls (operation=1)
        # to the MultiSend contract
        return self.create_transaction(
            SafeTransactionData(
                to=multi_send_address,
                value=0,
                data=data,
                operation=1,  # DelegateCall
            )
        )
