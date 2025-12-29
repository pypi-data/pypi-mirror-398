from ..imports import *

                              
def get_safe_password(password):
    safe_password = quote_plus(password)
    return safe_password
# Existing utility functions remain the same
def get_dbType(dbType=None):
    return dbType or 'database'

def get_dbName(dbName=None):
    return dbName or 'abstract'

def get_dbUser(dbUser=None):
    return dbUser

def verify_env_path(env_path=None):
    return env_path or get_env_path()
def get_db_vars_from_kwargs(**kwargs):
    """
    Normalize DB-related kwargs into canonical connection variables.

    Accepted aliases (case-insensitive):
        port        -> port
        password    -> password, pass
        dbType      -> type, dbtype
        host        -> host, url, address
        dbUser      -> user, dbuser
        dbName      -> dbname, database, name
    """
    resolved = {}

    key_aliases = {
        "port": ["port"],
        "password": ["password", "pass"],
        "dbType": ["type", "dbtype"],
        "host": ["host", "url", "address"],
        "user": ["user", "dbuser"],
        "dbname": ["dbname", "database", "name"],
        "env_path":["path","env_path"]
    }

    # Normalize incoming kwargs once
    lowered_kwargs = {k.lower(): v for k, v in kwargs.items()}

    for canonical_key, aliases in key_aliases.items():
        for alias in aliases:
            if alias in lowered_kwargs:
                resolved[canonical_key] = lowered_kwargs[alias]
                break  # stop searching aliases, not keys

    return resolved
def get_kwargs_dict(**kwargs):
    return kwargs
def get_db_env_value(dbname,user,env_path=None,**kwargs):
    env_path = verify_env_path(env_path)
    dbname_part_key=""
    user_part_key=""
    if dbname:
        dbname_part_key=f"{dbname}_"
    if user:
        user_part_key=f"{dbname_part_key}{user}_"
    for key,value in kwargs.items():
        value = get_env_value(value) or value
        if not value:
            for part_key in [dbname_part_key,user_part_key]:
                temp_key = f"{part_key}{key}"
                value = get_env_value(temp_key.upper(),path=env_path)
                if value:
                    break
        kwargs[key]=value
    return get_kwargs_dict(dbname=dbname,user=user,**kwargs)
def get_db_env_key(dbname=None,user=None,port=None,password=None,host=None,env_path=None,dbType=None):
    return get_db_env_value(dbname=dbname,user=user,port=port,password=password,host=host,env_path=env_path)
def derive_db_vars(**kwargs):
    db_vars = get_db_vars_from_kwargs(**kwargs)
    return get_db_env_key(**db_vars)
def get_db_vars(**kwargs):
    dbVars = derive_db_vars(**kwargs)
    protocol = 'postgresql'
    if 'rabbit' in str(dbVars.get('dbname',"")).lower():
        protocol = 'amqp'
    dbVars['dburl'] = f"{protocol}://{dbVars['user']}:{dbVars['password']}@{dbVars['host']}:{dbVars['port']}/{dbVars['dbname']}"
    return dbVars

