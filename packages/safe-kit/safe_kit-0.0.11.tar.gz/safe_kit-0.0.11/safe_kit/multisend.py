from hexbytes import HexBytes

from safe_kit.types import SafeTransactionData


class MultiSend:
    """
    Utilities for encoding MultiSend transactions.
    """

    @staticmethod
    def encode_transactions(transactions: list[SafeTransactionData]) -> bytes:
        """
        Encodes a list of SafeTransactionData into a single byte string
        compatible with the MultiSend contract.

        Format:
        operation (1 byte) + to (20 bytes) + value (32 bytes) +
        data_length (32 bytes) + data (bytes)
        """
        encoded_data = b""
        for tx in transactions:
            # operation: 1 byte
            operation = int(tx.operation).to_bytes(1, byteorder="big")

            # to: 20 bytes
            # Ensure it's bytes and 20 bytes long
            to_address = HexBytes(tx.to)
            if len(to_address) != 20:
                raise ValueError(f"Invalid address length for {tx.to}")

            # value: 32 bytes
            value = int(tx.value).to_bytes(32, byteorder="big")

            # data
            data = HexBytes(tx.data)
            data_length = len(data).to_bytes(32, byteorder="big")

            encoded_data += operation + to_address + value + data_length + data

        return encoded_data
