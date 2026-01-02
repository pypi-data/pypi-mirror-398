class PincodePackageError(Exception):
    """Base exception for pincode_package"""
    pass


class APIUnavailableError(PincodePackageError):
    """Raised when PostalPincode API is unreachable"""
    pass


class PincodeNotFoundError(PincodePackageError):
    """Raised when pincode is invalid or not found"""
    pass


class PostOfficeNotFoundError(PincodePackageError):
    """Raised when post office name is not found"""
    pass
