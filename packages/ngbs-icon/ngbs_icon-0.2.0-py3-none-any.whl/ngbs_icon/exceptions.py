class NgbsIconError(Exception):
    """Base exception for ngbs-icon."""


class TransportError(NgbsIconError):
    """Network / connection / timeout error."""


class ProtocolError(NgbsIconError):
    """Invalid or error response from device."""
