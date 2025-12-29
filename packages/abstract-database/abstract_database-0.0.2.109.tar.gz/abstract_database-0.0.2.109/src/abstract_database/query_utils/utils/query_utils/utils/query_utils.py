from .execute_utils import *
def get_all_table_names(schema='public'):
    """Fetch all table names from a specified schema."""
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE';
    """
    result = execute_query(query, values=(schema,), fetch=True, as_dict=False)
    return [row[0] for row in result] if result else []

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
