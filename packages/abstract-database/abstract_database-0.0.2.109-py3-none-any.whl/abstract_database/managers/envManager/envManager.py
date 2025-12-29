from .utils import *
class envManager(metaclass=SingletonMeta):
    def __init__(self):
        if not hasattr(self, 'initialized'):
          self.initialized = True
          self.tables_dir = '/home/computron/Desktop/shovel/real_estate_grabber/readable/realestate_tables_config.json'
          self.env_path = '/home/computron/Desktop/shovel/real_estate_grabber/readable/.env'
          self.dbType = 'database'
          self.insert_list_file = 'realestate_tables_config.json'
          self.insert_list_path = os.path.join(self.tables_dir, self.insert_list_file)
          self.repo = {}
          self.initialized = True
    
    def var_check(self, dbName, dbType=None):
        dbType = dbType or self.dbType
        if dbName not in self.repo:
            self.repo[dbName] = {}
        if dbType not in self.repo[dbName]:
            self.repo[dbName][dbType] = {
                "env_path": self.env_path,
                "tables_dir": self.tables_dir,
                "insert_list_file": self.insert_list_file,
                "insert_list_path": self.insert_list_path
            }

    def add_to_memory(self, dbName, dbType=None, env_path=None, tables_dir=None, insert_list_file=None,insert_list_path=None,tables=None,table=None):
        dbType = dbType or self.dbType
        self.var_check(dbName, dbType=dbType)
        env_path = env_path or self.repo[dbName][dbType]["env_path"]
        tables_dir = tables_dir or self.repo[dbName][dbType]["tables_dir"]
        
        insert_list_file = insert_list_file or create_insert_list_file(dbName, dbType=dbType)
        insert_list_path = insert_list_path or os.path.join(tables_dir, insert_list_file)
        
        dbVars = self.get_db_vars(dbName, dbType=dbType, env_path=env_path)
        tables = tables or safe_read_from_json(insert_list_path)
        table = table or get_table_from_tables(dbName,tables)
        self.repo[dbName][dbType] = {
            "env_path": env_path,
            "tables_dir": tables_dir,
            "dbVars": dbVars,
            "insert_list_file": insert_list_file,
            "insert_list_path": insert_list_path,
            "tables": tables,
            "table":table,
            "conn_mgr": self.get_conn_mgr(dbName=dbName, dbType=dbType, env_path=env_path, tables=tables, dbVars=dbVars)
        }

    def get_from_memory(self, dbName, dbType=None, variable=None):
        dbType = dbType or self.dbType
        self.var_check(dbName, dbType=dbType)
        return self.repo[dbName][dbType].get(variable, self.repo[dbName][dbType])

    def get_db_url(self, dbName, dbType=None, dbVars=None, env_path=None):
        dbType = dbType or self.dbType
        protocol = 'postgresql' if 'rabbit' not in dbType.lower() else 'amqp'
        dbVars = dbVars or self.get_db_vars(dbName=dbName, dbType=dbType, env_path=env_path)
        dbVars['dburl'] = f"{protocol}://{dbVars['user']}:{dbVars['password']}@{dbVars['host']}:{dbVars['port']}/{dbVars['dbname']}"
        return dbVars

    def get_db_vars(self, dbName, dbType=None, env_path=None):
        dbType = dbType or self.dbType
        env_path = env_path or self.get_from_memory(dbName, dbType=dbType, variable="env_path")
        dbVars = {"user": None, "dbname": None, "host": None, "port": None, "password": None}
        for key in dbVars:
            dbVars[key] = get_pure_env_value(key=get_db_key(dbName, dbType, key), path=env_path)
        return self.get_db_url(dbName=dbName, dbType=dbType, dbVars=dbVars, env_path=env_path)

    def get_conn_mgr(self, dbName, dbType=None, env_path=None, tables=None, dbVars=None):
        dbType = dbType or self.dbType
        env_path = env_path or self.get_from_memory(dbName, dbType=dbType, variable="env_path")
        tables = tables or get_insert_list(dbName, dbType=dbType)
        dbVars = dbVars or self.get_db_vars(dbName=dbName, dbType=dbType, env_path=env_path)
        return connectionManager(dbName=dbName, dbType=dbType, env_path=env_path, tables=tables, dbVars=dbVars)


