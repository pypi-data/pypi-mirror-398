class DatabaseError(Exception):
    pass

class IntegrityError(DatabaseError):
    pass

class OperationalError(DatabaseError):
    pass

class ProgrammingError(DatabaseError):
    pass

class NotSupportedError(DatabaseError):
    pass

class DataError(DatabaseError):
    pass

class InternalError(DatabaseError):
    pass
