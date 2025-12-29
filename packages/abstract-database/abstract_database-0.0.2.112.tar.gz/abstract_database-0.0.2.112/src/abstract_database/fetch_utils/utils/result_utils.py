from ..imports import columnNamesManager,get_all_table_names
def get_column_names(tableName,schema='public'):
    input(tableName)
    return columnNamesManager().get_column_names(tableName,schema)
def getZipRows(tableName, rows, schema='public'):
    columnNames = get_column_names(tableName,schema)
    if columnNames:
        return [dict(zip(columnNames,row)) for row in make_list(rows) if row]
def get_db_from(tableName=None,columnNames=None,searchColumn=None,searchValue=None,count=False,zipit=True):
    columnNames=columnNames or '*'
    if isinstance(columnNames,list):
        columnNames = ','.join(columnNames)
    response = fetch_any_combo(tableName=tableName,columnNames=columnNames,searchColumn=searchColumn,searchValue=searchValue,zipit=zipit,count=count)
    return response
def get_all_table_info(schema='public'):
    all_table_infos = {each:get_column_names(each) for each in get_all_table_names()}
    return all_table_infos

