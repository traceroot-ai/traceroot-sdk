from traceroot.logger import get_logger
from traceroot.tracer import _initialize_tracing as init
from traceroot.tracer import trace

init()

__all__ = [
    'init',
    'trace',
    'get_logger',
]
