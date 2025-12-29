# /var/www/abstractendeavors/secure-files/big_man/flask_app/login_app/functions/query_utils.py
from ..imports import (get_env_value,
                          RealDictCursor,
                          psycopg2,
                          logging,
                          warnings,
                          traceback,
                          sql,
                          make_list,
                          SingletonMeta,
                          initialize_call_log
                          )
from ..managers.connectionManager import connectionManager,connect_db
# Initialize connectionManager once (using your .env path if needed)
connectionManager(env_path="/home/solcatcher/.env",
                  dbType='database',
                  dbName='abstract')


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)
def get_connection():
    return connect_db()
def execute_query(query, *args,**kwargs):
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
    dict_vars = {'fetch':True,'as_dict':True,'values':args}
    kwargs_copy = kwargs.copy()
    for key,value in dict_vars.items():
        if key in kwargs:
            value = kwargs[key] or value
        dict_vars[key] =  value
        if key in kwargs:
            del kwargs[key]
    # Convert Composed query to string if necessary
    if isinstance(query, sql.Composed):
        query_str = query.as_string(get_connection())
    else:
        query_str = str(query)
    values = dict_vars.get('values',set())
    logger.info(f"Executing query: {query_str} with values: {values}")
    conn = get_connection()
    cursor_factory = RealDictCursor if dict_vars['as_dict'] else None
        
    try:
        with conn.cursor(cursor_factory=cursor_factory) as cursor:
            cursor.execute(query, values)
            if dict_vars['fetch'] and query_str.strip().upper().startswith("SELECT"):
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

def get_all_table_names(schema='public'):
    """Fetch all table names from a specified schema."""
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE';
    """
    results = execute_query(query, values=(schema,), fetch=True, as_dict=False)
    rows = get_rows(results)
    return [row.get('table_name') for row in rows]
def get_table_info(table_name,schema='public'):
    """Fetch all table names from a specified schema."""
    query = """f"SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT 1;"""
    results = execute_query(query)
    rows = get_rows(results)
    return rows
def print_all_tables(queries):
    for key,value in queries.items():
        print(f"{key}: {value}\n\n")
# Legacy functions with deprecation warnings
def query_data_as_dict(query, values=None, error="Error executing query:"):
    warnings.warn("query_data_as_dict is deprecated; use execute_query instead.", DeprecationWarning)
    return execute_query(query=query, values=values, fetch=True, as_dict=True)

def get_query_result(query, values=None, zipit=False, **kwargs):
    warnings.warn("get_query_result is deprecated; use execute_query instead.", DeprecationWarning)
    return execute_query(query, values=values, fetch=True, as_dict=zipit)

def query_data(query, values=None, error="Error executing query:", zipRows=True):
    warnings.warn("query_data is deprecated; use execute_query instead.", DeprecationWarning)
    logger.info(f"query = {query} and values = {values}")
    return execute_query(query, values=values, fetch=True, as_dict=zipRows)

def aggregate_rows(query, values=None, errorMsg='Error Fetching Rows', fetch=True, as_dict=None, zipRows=None, zipit=None, **kwargs):
    warnings.warn("aggregate_rows is deprecated; use execute_query instead.", DeprecationWarning)
    # Resolve as_dict from multiple possible parameters
    resolved_as_dict = as_dict if as_dict is not None else (zipRows if zipRows is not None else (zipit if zipit is not None else True))
    return execute_query(query, values=values, fetch=fetch, as_dict=resolved_as_dict)

def get_rows(rows):
    if not rows:
        return None
    
    if isinstance(rows,psycopg2.extras.RealDictRow):
        rows = dict(rows)
    if isinstance(rows, list):
        for i,row in  enumerate(rows):
            if isinstance(row,psycopg2.extras.RealDictRow):
                row = dict(row)
            rows[i] = row
    # If select_rows returned a dict, use it; if it returned a list, grab the first item
    if isinstance(rows, dict):
        return rows
    else:
        return rows
def get_cur_conn(use_dict_cursor=True):
    """
    Get a database connection and a RealDictCursor.
    Returns:
        tuple: (cursor, connection)
    """
    conn = connectionManager().get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) if use_dict_cursor else conn.cursor()
    return cur, conn
def select_all(query: str, *args):
    """
    Execute a SELECT query that returns zero or more rows.
    Returns:
        list[dict]: list of rows, empty if none.
    """
    cur, conn = get_cur_conn()
    try:
        cur.execute(query, args) if args else cur.execute(query)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()
def insert_query(query: str, *args):
    cur, conn = get_cur_conn()
    try:
        cur.execute(query, args)
        # if there was a RETURNING clause, fetch it:
        try:
            new_id = cur.fetchone()['id']
        except (psycopg2.ProgrammingError, TypeError):
            new_id = None
        conn.commit()
        return new_id
    finally:
        cur.close()
        conn.close()

def select_distinct_rows(query: str, *args):
    """
    Execute a SELECT query that returns zero or more rows.
    Returns:
        list[dict]: a list of RealDictCursor rows (dicts), empty if none.
    """
    cur, conn = get_cur_conn()
    try:
        if args:
            cur.execute(query, args)
        else:
            cur.execute(query)
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()

def select_rows(query: str, *args):
    """
    Execute a SELECT query that returns a single row or None.
    Args:
        query (str): The SQL query with %s placeholders.
        *args: Parameters to substitute into the query.
    Returns:
        A dictionary if a row is found, else None.
    """
    print("DEBUG select_rows—type(query):", type(query), " value:", query)
    cur, conn = get_cur_conn()
    try:
        if args:
            cur.execute(query, args)
        else:
            cur.execute(query)
        row = cur.fetchone()
        return row or []
    finally:
        cur.close()
        conn.close()
