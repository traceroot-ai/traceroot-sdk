from traceroot.logger import get_logger
from traceroot.tracer import init, shutdown, trace

__version__ = '0.0.5'

from dotenv import load_dotenv

load_dotenv()

init()

__all__ = [
    'init',
    'trace',
    'get_logger',
    'shutdown',
]
