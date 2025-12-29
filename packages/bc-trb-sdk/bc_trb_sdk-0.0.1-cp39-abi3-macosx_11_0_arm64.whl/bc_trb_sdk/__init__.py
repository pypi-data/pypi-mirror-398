"""
bc_trb SDK - Python bindings for EEG-CES device communication.

This package provides a Python interface to the bc_trb SDK for EEG data acquisition.

Example:
    >>> from bc_trb_sdk import open_bc_trb_usb
    >>> device = open_bc_trb_usb()
    >>> print("TriggerBox device connected")
"""

__version__ = "0.1.0"

# Import from the Rust extension module
from ._native import (
    # Enums
    LogLevel,

    # Model types
    DeviceApi,
    DeviceInfo,

    # TriggerBox types
    TrbAdcValue,
    TrbConfig,
    TrbStatus,
    TriggerApi,

    # DeviceApi functions - TriggerBox
    open_bc_trb_usb,

)

__all__ = [
    # Enums
    "LogLevel",

    # Model types
    "DeviceApi",
    "DeviceInfo",

    # TriggerBox types
    "TrbAdcValue",
    "TrbConfig",
    "TrbStatus",
    "TriggerApi",

    # DeviceApi functions - TriggerBox
    "open_bc_trb_usb",

]