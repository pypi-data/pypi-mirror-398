from .envManager import *
def get_table(dbName, dbType=None):
    return envManager().get_from_memory(dbName, dbType=dbType, variable="table")

def get_tables_dir(dbName, dbType=None):
    return envManager().get_from_memory(dbName, dbType=dbType, variable="tables_dir")

def get_env_path(dbName, dbType=None):
    return envManager().get_from_memory(dbName, dbType=dbType, variable="env_path")

def get_insert_list_path(dbName, dbType=None):
    return envManager().get_from_memory(dbName, dbType=dbType, variable="insert_list_path")

def get_conn_mgr(dbName, dbType=None, env_path=None, tables=None):
    return envManager().get_from_memory(dbName, dbType=dbType, variable="conn_mgr")

def get_insert_list(dbName, dbType=None):
    return envManager().get_from_memory(dbName=dbName, dbType=dbType,variable="tables")

def getInsertType(tableName=None, table_configurations=None, dbName=None, dbType=None):
    table_configurations = table_configurations or get_insert_list(dbName=dbName, dbType=dbType)
    insertList = [ls for ls in table_configurations if ls.get("tableName").lower() == tableName.lower()]
    return insertList[0] if insertList else None

def dump_if_dict(obj):
    return json.dumps(obj) if isinstance(obj, dict) else obj
