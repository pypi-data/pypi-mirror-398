# src/abstract_database/fetch_utils/fetch_utils/insert_utils.py

from ..utils.build_utils import build_return_clause
from ..utils.build_utils import map_parts_vals
from ..imports import query_data, sql

def insert_any_combo(
    *,
    table_name: str,
    insert_map: dict,
    returning=False,   # False | True | 'count' | 'col1,col2'
    zipit=True,
    schema='public',
) -> list[dict]:
    """
    Dynamically INSERT into `schema.table_name` with columns and values
    from `insert_map`. Optionally RETURNING columns.

    Returns:
      - If returning==False: []
      - If returning==True: list of full rows
      - If returning=='count': [{'count': n}]
      - If returning='col1,col2': list of dicts with those cols
    """
    if not table_name or table_name == '*':
        raise ValueError("table_name is required")
    if not insert_map:
        raise ValueError("insert_map cannot be empty")

    # build the INSERT INTO <schema>.<table> (<cols>) VALUES (%s, %s, …)
    cols = [sql.Identifier(c) for c in insert_map.keys()]
    parts, values = map_parts_vals(insert_map, vals=[], any_value=False)
    col_list = sql.SQL(', ').join(cols)
    placeholder_list = sql.SQL(', ').join(sql.SQL('%s') for _ in parts)

    base = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
        sql.Identifier(schema),
        sql.Identifier(table_name),
        col_list,
        placeholder_list
    )

    # handle RETURNING clause
    return_sql = build_return_clause(returning)

    qry = base + return_sql

    return query_data(qry, values=values, zipRows=zipit)
