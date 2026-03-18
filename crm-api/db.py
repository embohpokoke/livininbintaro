"""
Livininbintaro CRM — Database (PostgreSQL with SQLite-compatible interface)
Updated: 2026-03-11 - Fixed lastrowid support for PostgreSQL
Schema: crm
"""

import psycopg2
import psycopg2.pool
import re
from config import DATABASE_URL, DB_SCHEMA

# Connection pool
connection_pool = None


class DictRow(dict):
    """Dict that also supports integer indexing like SQLite Row"""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class PostgreSQLiteCursor:
    """Cursor wrapper that returns SQLite-compatible rows"""
    
    def __init__(self, cursor, conn=None):
        self._cursor = cursor
        self._conn = conn
        self._lastrowid = None
    
    @property
    def lastrowid(self):
        """Get last inserted row id (PostgreSQL compatible)"""
        return self._lastrowid
    
    def set_lastrowid(self, rowid):
        self._lastrowid = rowid
    
    def _make_dict_row(self, row):
        """Convert tuple row to DictRow using column names"""
        if row is None:
            return None
        if not self._cursor.description:
            return row
        columns = [desc[0] for desc in self._cursor.description]
        return DictRow(zip(columns, row))
    
    def fetchone(self):
        row = self._cursor.fetchone()
        return self._make_dict_row(row)
    
    def fetchall(self):
        rows = self._cursor.fetchall()
        return [self._make_dict_row(row) for row in rows]
    
    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size)
        return [self._make_dict_row(row) for row in rows]
    
    def __iter__(self):
        for row in self._cursor:
            yield self._make_dict_row(row)


class PostgreSQLiteConnection:
    """Wrapper to make PostgreSQL behave like SQLite for minimal code changes"""
    
    def __init__(self, conn):
        self._conn = conn
        self._cursor = None
        with self._conn.cursor() as cur:
            cur.execute(f"SET search_path TO {DB_SCHEMA}, public")
        self._conn.commit()
    
    def execute(self, sql, params=None):
        """Execute SQL and return cursor-like object"""
        # Convert ? to %s for PostgreSQL
        sql = sql.replace("?", "%s")
        
        # Auto-add RETURNING id for INSERT statements without it
        sql_upper = sql.strip().upper()
        needs_returning = sql_upper.startswith("INSERT") and "RETURNING" not in sql_upper
        if needs_returning:
            sql = sql.rstrip().rstrip(";") + " RETURNING id"
        
        # Create cursor
        cursor = self._conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        self._cursor = cursor
        
        # Wrap cursor
        wrapped = PostgreSQLiteCursor(cursor, self._conn)
        
        # Get lastrowid if this was an INSERT with RETURNING
        if needs_returning:
            try:
                row = cursor.fetchone()
                if row:
                    wrapped.set_lastrowid(row[0])
            except psycopg2.ProgrammingError:
                pass  # No results to fetch
        
        return wrapped
    
    def executescript(self, script):
        """Execute multiple SQL statements (for init_db compatibility)"""
        pass
    
    def commit(self):
        self._conn.commit()
    
    def rollback(self):
        self._conn.rollback()
    
    def close(self):
        if self._cursor:
            self._cursor.close()
        if connection_pool:
            connection_pool.putconn(self._conn)
    
    @property
    def row_factory(self):
        return None
    
    @row_factory.setter
    def row_factory(self, factory):
        pass


def init_pool():
    """Initialize connection pool"""
    global connection_pool
    if connection_pool is None:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=2,
            maxconn=20,
            dsn=DATABASE_URL
        )


def get_db():
    """Get database connection (SQLite-compatible interface)"""
    if connection_pool is None:
        init_pool()
    
    conn = connection_pool.getconn()
    return PostgreSQLiteConnection(conn)


def normalize_phone(phone) -> str:
    """Normalize phone number to international format"""
    if phone is None:
        return ""
    s = str(phone).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = re.sub(r"[^\d]", "", s)
    if s.startswith("0"):
        s = "62" + s[1:]
    if s.startswith("+"):
        s = s[1:]
    return s


def init_db():
    """Initialize database - tables already created via migration"""
    init_pool()
    print("✅ PostgreSQL connection pool initialized")


def migrate_db():
    """Migrations handled by migration script"""
    pass


def close_pool():
    """Close all connections in the pool"""
    global connection_pool
    if connection_pool is not None:
        connection_pool.closeall()
        connection_pool = None
