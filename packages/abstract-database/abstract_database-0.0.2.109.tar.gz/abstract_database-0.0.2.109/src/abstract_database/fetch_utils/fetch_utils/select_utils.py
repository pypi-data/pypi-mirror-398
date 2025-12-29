from ..utils import build_return_clause,select_column_names,build_where_clause
from ..imports import query_data,sql
def fetch_any_combo(*,
                    column_names='*',
                    table_name,
                    search_map=None,
                    count=False,
                    any_value=False,
                    returning=False,        # False | True | 'count' | 'col1,col2'
                    zipit=True,
                    schema='public'):

    if not table_name or table_name == '*':
        logger.error("Invalid table_name provided to fetch_any_combo: %s", table_name)
        return []
    search_map = search_map or {}
    select_cols = select_column_names(column_names)
    base = sql.SQL("SELECT {} FROM {}.{}").format(
        select_cols,
        sql.Identifier(schema),
        sql.Identifier(table_name)
    )
    where_sql, values = build_where_clause(
        search_map,
        any_value=any_value)
    return_sql = build_return_clause(returning=returning)
    qry = (
        base
        + where_sql
        + return_sql
    )

    return query_data(qry, values=values, zipRows=zipit)


