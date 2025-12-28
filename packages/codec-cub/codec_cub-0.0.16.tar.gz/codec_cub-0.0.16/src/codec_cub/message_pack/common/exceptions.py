"""A module defining exceptions for MessagePack operations."""


class PackError(TypeError):
    """Exception raised for errors in the packing process."""


class UnpackError(ValueError):
    """Exception raised for errors in the unpacking process."""


class InvalidMsgPackTagError(ValueError):
    """Exception raised for invalid MessagePack tags."""
