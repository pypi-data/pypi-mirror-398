class FXProtocolError(Exception):
    """Base exception for all f(x) Protocol SDK errors."""
    pass

class TransactionFailedError(FXProtocolError):
    """Raised when a blockchain transaction fails."""
    pass

class InsufficientBalanceError(FXProtocolError):
    """Raised when the user has insufficient balance for an operation."""
    pass

class ContractCallError(FXProtocolError):
    """Raised when a read call to a contract fails."""
    pass

class InvalidAddressError(FXProtocolError):
    """Raised when an invalid Ethereum address is provided."""
    pass

class ConfigurationError(FXProtocolError):
    """Raised when the SDK is misconfigured."""
    pass

