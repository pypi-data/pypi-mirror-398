from .main import *


# Functions to interact with the connection manager
def create_connection(**kwargs):
    return connectionManager(**kwargs)

def get_db_connection(**kwargs):

    return connectionManager(**kwargs).get_db_connection()

def put_db_connection(conn):
    connectionManager().put_db_connection(conn)

def connect_db(**kwargs):
    return connectionManager(**kwargs).connect_db()

def get_insert(tableName,**kwargs):
    return connectionManager(**kwargs).get_insert(tableName)

def fetchFromDb(tableName, searchValue,**kwargs):
    return connectionManager(**kwargs).fetchFromDb(tableName, searchValue)

def insertIntoDb(tableName, searchValue, insertValue,**kwargs):
    return connectionManager(**kwargs).insertIntoDb(tableName, searchValue, insertValue)

def search_multiple_fields(query, **kwargs):
    return connectionManager().search_multiple_fields(query, **kwargs)

def get_first_row_as_dict(tableName=None, rowNum=1):
    return connectionManager().get_first_row_as_dict(tableName, rowNum)
def get_cur_conn(use_dict_cursor=True):
    """
    Get a database connection and a RealDictCursor.
    Returns:
        tuple: (cursor, connection)
    """
    conn = connectionManager().get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) if use_dict_cursor else conn.cursor()
    return cur, conn
