from ..imports import *
def get_db_key(dbName, dbType, extra=None):
    key = f"{dbName.upper()}_{dbType.upper()}"
    if extra:
        key += f"_{extra.upper()}"
    return key

def get_bot_name():
    return 'darnell'

def get_pure_env_value(key=None, path=None):
    return get_env_value(path=path or get_env_path(), key=key)

def get_bot_env_key(key):
    return get_env_value(path=get_env_path(), key=f"{get_bot_name()}_{key}")

def get_env_key(key, path=None):
    return get_pure_env_value(path=path or get_env_path(), key=key)

def get_open_ai_key():
    return get_env_key('open_ai')

def get_discord_token():
    return get_env_key('token')

def get_application_id():
    return get_env_key('application_id')

def get_client_id():
    return get_env_key('client_id')

def get_client_secret():
    return get_env_key('client_secret')

def get_public_key():
    return get_env_key('public_key')

def get_dbType(dbType=None):
    return f"_{dbType}" if dbType else ''

def create_insert_list_file(dbName, dbType=None):
    return f"{dbName}{get_dbType(dbType)}_table_config.json"

def get_table_from_tables(dbName,tables=None):
  dbName_lower = str(dbName).lower()
  tables = tables or get_insert_list(dbName)
  
  for table in tables:
    if dbName_lower in table.get('tableName').lower():
        return table
