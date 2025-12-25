from typing import Optional, Any
from .storage.engine import StorageEngine
from .schema.metadata import SchemaManager
from .index.manager import IndexManager
from .security.hasher import BLAKE2Hasher
from .query.executor import QueryExecutor
from .transaction.manager import TransactionManager, Transaction
from .cursor import Cursor
from .utils.exceptions import OperationalError, ProgrammingError
import pickle

class Connection:
    def __init__(self, database: str, compression_level: int = 6):
        self.database = database
        self.storage = StorageEngine(database, compression_level)
        self.schema = SchemaManager()
        self.index_manager = IndexManager()
        self.hasher = BLAKE2Hasher()
        self.executor = QueryExecutor(self.storage, self.schema, self.index_manager, self.hasher)
        self.transaction_manager = TransactionManager()
        self.is_closed = False
        
        self._load_schema()
    
    def _load_schema(self):
        try:
            meta_page = self.storage.get_page(0)
            if meta_page and meta_page.header.record_count > 0:
                schema_data = meta_page.read_record(0, len(meta_page.data) - meta_page.get_free_space())
                if schema_data and schema_data != b'\x00' * len(schema_data):
                    self.schema = SchemaManager.deserialize(schema_data)
                    
                    if hasattr(self.executor, 'table_pages'):
                        for table_name in self.schema.list_tables():
                            if table_name not in self.executor.table_pages:
                                self.executor.table_pages[table_name] = []
        except:
            pass
    
    def _save_schema(self):
        schema_data = self.schema.serialize()
        meta_page = self.storage.get_page(0)
        if not meta_page:
            meta_page = self.storage.allocate_page()
        
        meta_page.clear()
        meta_page.write_record(0, schema_data)
    
    def cursor(self) -> Cursor:
        if self.is_closed:
            raise ProgrammingError("Cannot create cursor on closed connection")
        return Cursor(self)
    
    def commit(self):
        if self.is_closed:
            raise ProgrammingError("Cannot commit on closed connection")
        
        if self.transaction_manager.has_active_transaction():
            transaction = self.transaction_manager.get_active_transaction()
            self.transaction_manager.commit_transaction(transaction)
        
        self._save_schema()
        self.storage.flush()
    
    def rollback(self):
        if self.is_closed:
            raise ProgrammingError("Cannot rollback on closed connection")
        
        if self.transaction_manager.has_active_transaction():
            transaction = self.transaction_manager.get_active_transaction()
            self.transaction_manager.rollback_transaction(transaction)
    
    def close(self):
        if not self.is_closed:
            self.commit()
            self.storage.close()
            self.is_closed = True
    
    def execute(self, sql: str, parameters: tuple = None) -> Cursor:
        cursor = self.cursor()
        cursor.execute(sql, parameters)
        return cursor
    
    def executemany(self, sql: str, seq_of_parameters) -> Cursor:
        cursor = self.cursor()
        cursor.executemany(sql, seq_of_parameters)
        return cursor
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
    
    def __del__(self):
        if not self.is_closed:
            self.close()

def connect(database: str, compression_level: int = 6) -> Connection:
    return Connection(database, compression_level)
