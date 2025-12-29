from ..imports import *
from .....managers.connectionManager import connectionManager,connect_db
logger = get_logFile('query_utils')
def get_connection():
    return connect_db()
def execute_query(query, values=None, fetch=True, as_dict=True):
    """
    Execute a SQL query and return results if applicable.
    
    Args:
        query (str or psycopg2.sql.Composed): SQL query to execute.
        values (tuple, optional): Values for parameterized queries.
        fetch (bool): Whether to fetch results (for SELECT) or commit (for INSERT/UPDATE).
        as_dict (bool): Return results as dictionaries if True, else as tuples.
    
    Returns:
        list: Query results (empty if no fetch or error).
    """
    # Convert Composed query to string if necessary
    if isinstance(query, sql.Composed):
        query_str = query.as_string(get_connection())
    else:
        query_str = str(query)

    logger.info(f"Executing query: {query_str} with values: {values}")
    conn = get_connection()
    cursor_factory = RealDictCursor if as_dict else None
    
    try:
        with conn.cursor(cursor_factory=cursor_factory) as cursor:
            cursor.execute(query_str, values)
            if fetch and query_str.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
                if result:
                    logger.debug(f"First row: {result[0]}")
                return result
            conn.commit()
            return []
    except Exception as e:
        conn.rollback()
        logger.error(f"Query failed: {query_str}\nValues: {values}\nError: {e}\n{traceback.format_exc()}")
        return []
    finally:
        conn.close()
