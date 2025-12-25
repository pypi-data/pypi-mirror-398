from .connection import connect, Connection
from .cursor import Cursor
from .utils.exceptions import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    ProgrammingError,
    NotSupportedError
)

__version__ = "1.1.2"
__author__ = "RibbitX Team"
__all__ = [
    "connect",
    "Connection",
    "Cursor",
    "DatabaseError",
    "IntegrityError",
    "OperationalError",
    "ProgrammingError",
    "NotSupportedError",
]

PARSE_DECLTYPES = 1
PARSE_COLNAMES = 2

try:
    from .server import RibbitXDBServer, start_server
    __all__.extend(['RibbitXDBServer', 'start_server'])
except ImportError:
    pass

try:
    from .client import NetworkConnection, NetworkCursor
    __all__.extend(['NetworkConnection', 'NetworkCursor'])
except ImportError:
    pass

try:
    from .pool import ConnectionPool, PooledConnection
    __all__.extend(['ConnectionPool', 'PooledConnection'])
except ImportError:
    pass

try:
    from .batch import BatchOperations
    __all__.extend(['BatchOperations'])
except ImportError:
    pass

try:
    from .backup import DatabaseBackup, DatabaseRestore
    __all__.extend(['DatabaseBackup', 'DatabaseRestore'])
except ImportError:
    pass

try:
    from .advanced import SubqueryExecutor, CTEExecutor, WindowFunctionExecutor
    __all__.extend(['SubqueryExecutor', 'CTEExecutor', 'WindowFunctionExecutor'])
except ImportError:
    pass

def connect_network(host: str, port: int = 5432, user: str = None, 
                   password: str = None, **kwargs):
    from .client import NetworkConnection
    conn = NetworkConnection(host, port, user, password, **kwargs)
    conn.connect()
    return conn

