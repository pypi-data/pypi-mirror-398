from ..imports import psycopg2,RealDictCursor

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
