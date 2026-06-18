import sqlite3
from src.ports.uow import UnitOfWorkPort
from src.adapters.persistence.sqlite_repository import SQLitePaisRepository, SQLiteRegistroDiabetesRepository, SQLiteAuditLogRepository

class SQLiteUnitOfWork(UnitOfWorkPort):
    def __init__(self, db_path: str = "diabetes.db"):
        self.db_path = db_path
        self.conn = None

    def __enter__(self) -> 'SQLiteUnitOfWork':
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.paises = SQLitePaisRepository(self.conn)
        self.registros = SQLiteRegistroDiabetesRepository(self.conn)
        self.logs = SQLiteAuditLogRepository(self.conn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        if self.conn:
            self.conn.close()

    def commit(self) -> None:
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        if self.conn:
            self.conn.rollback()
