from .otel import get_logger as get_logger, get_propagation_headers as get_propagation_headers, initialize_otel as initialize_otel, shutdown_otel as shutdown_otel
from .otel_settings import OTelSettings as OTelSettings
from _typeshed import Incomplete

__all__ = ['OTelSettings', 'initialize_otel', 'shutdown_otel', 'get_logger', 'get_propagation_headers', '__version__']

__version__: Incomplete
