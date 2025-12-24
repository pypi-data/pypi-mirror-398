import importlib.metadata

from .pulse_eight_matrix_client import PulseEightMatrixClient
from .caching_pulse_eight_matrix_client import CachingPulseEightMatrixClient
from .exceptions import PulseEightError, PulseEightConnectionError, PulseEightAPIError
from .models import SystemDetails, SystemFeatures, Port, InputPortDetails, OutputPortDetails, SetPortResponse

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

__all__ = [
    "PulseEightMatrixClient",
    "CachingPulseEightMatrixClient",
    "PulseEightError",
    "PulseEightConnectionError",
    "PulseEightAPIError",
    "SystemDetails",
    "SystemFeatures",
    "Port",
    "InputPortDetails",
    "OutputPortDetails",
    "SetPortResponse",
]
