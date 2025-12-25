class SafeKitError(Exception):
    """Base exception for safe-kit"""

    pass


class SafeTransactionError(SafeKitError):
    """Exception raised when a Safe transaction fails"""

    def __init__(self, message: str, error_code: str | None = None):
        self.error_code = error_code
        super().__init__(f"{error_code}: {message}" if error_code else message)


class SafeServiceError(SafeKitError):
    """Exception raised when the Safe Transaction Service returns an error"""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(f"Status {status_code}: {message}" if status_code else message)


SAFE_ERRORS = {
    "GS000": "Could not finish initialization",
    "GS001": "Threshold needs to be defined",
    "GS010": "Not enough gas to execute Safe transaction",
    "GS011": "Could not pay gas costs with ether",
    "GS012": "Could not pay gas costs with token",
    "GS013": "Safe transaction failed when gasPrice and safeTxGas were 0",
    "GS020": "Signatures data too short",
    "GS021": "Invalid signature provided",
    "GS022": "Invalid signature provided (duplicate)",
    "GS023": "Invalid signature provided (not owner)",
    "GS024": "Invalid signature provided (not sorted)",
    "GS025": "Invalid signature provided (v is 0)",
    "GS026": "Invalid signature provided (v > 30)",
    "GS030": "Only owners can approve a hash",
    "GS031": "Hash has already been approved",
    "GS100": "Modules have already been initialized",
    "GS130": "New owner cannot be the null address",
}


def handle_contract_error(e: Exception) -> Exception:
    """
    Parses a web3 exception and returns a more readable SafeKitError if possible.
    """
    error_str = str(e)

    # Check for Safe error codes in the exception message
    for code, message in SAFE_ERRORS.items():
        if code in error_str:
            return SafeTransactionError(message, error_code=code)

    # If no specific Safe error is found, return the original exception
    # or wrap it in a generic SafeKitError
    return e
