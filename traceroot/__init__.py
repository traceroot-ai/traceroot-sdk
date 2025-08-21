from traceroot.logger import get_logger
from traceroot.tracer import _initialize_tracing as init
from traceroot.tracer import shutdown, trace

__version__ = '0.0.4a12'

init()

__all__ = [
    'init',
    'trace',
    'get_logger',
    'shutdown',
]
