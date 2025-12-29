from .utils import *
class connectionManager(metaclass=SingletonMeta):
        
    def __init__(self, tables=[], tables_path=None,**kwargs):
        if not hasattr(self, 'initialized'):
            self.initialized=True
            dbVars = derive_db_vars(**kwargs)
            self.env_path = dbVars.get('env_path')
            self.dbName = dbVars.get('dbname')
            self.dbType = dbVars.get('dbtype')
            self.dbUser = dbVars.get('user')
            self.dbVars = self.get_db_vars(**dbVars)
            self.user = self.dbUser = self.dbVars['user']
            self.password = self.dbVars['password']
            self.host = self.dbVars['host']
            self.port = self.dbVars['port']
            self.dbname = self.dbVars['dbname']
            self.dburl = self.dbVars['dburl']  # URL-based connection string
            self.table_mgr = TableManager()
            self.tables = tables or safe_load_from_json(file_path=tables_path) or []
            self.table_mgr.env_path = self.env_path
            self.add_insert_list=None
            
            self.check_conn()
        
    def check_conn(self):
        if self.add_insert_list == None:
          try:
                self.table_mgr.add_insert_list(self.connect_db(), self.tables, self.dbName)
                self.table_mgr.add_insert_list(self.connect_db(), self.tables, self.dbName)
                self.add_insert_list=True
          except:
            pass
        return self.add_insert_list
    def get_dbName(self, dbName=None):
        return get_dbName(dbName=dbName or self.dbName)
    def get_dbType(self, dbType=None):
        return get_dbType(dbType=dbType or self.dbType)
    def get_dbUser(self, dbUser=None):
        return get_dbUser(dbUser=dbUser or self.dbUser)
    def get_env_path(self, env_path=None):
        return verify_env_path(env_path=env_path)

    def get_db_vars(self,**kwargs):
        return get_db_vars(**kwargs)

    def change_db_vars(self, tables=[], tables_path=None,**kwargs):
        dbVars = derive_db_vars(**kwargs)
        self.env_path = dbVars.get('env_path')
        self.dbName = dbVars.get('dbname')
        self.dbType = dbVars.get('dbtype')
        self.dbUser = dbVars.get('user')
        self.dbVars = self.get_db_vars(**dbVars)
        self.user = self.dbUser = self.dbVars['user']
        self.password = self.dbVars['password']
        self.host = self.dbVars['host']
        self.port = self.dbVars['port']
        self.dbname = self.dbVars['dbname']
        self.dburl = self.dbVars['dburl']  # URL-based connection string
        self.simple_connect = self.simple_connect_db()
        self.get_db_connection(self.connect_db())
        self.tables = tables or self.tables
        self.table_mgr.add_insert_list(self.connect_db(), self.tables, self.dbName)
        return self.dbVars

    def connect_db(self):
            
            """ Establish a connection to the database, either by connection parameters or via URL """
            if self.dburl:
                
                return psycopg2.connect(self.dburl)
            else:
                return psycopg2.connect(user=self.user,
                                        password=self.password,
                                        host=self.host,
                                        port=self.port,
                                        dbname=self.dbname)

    def simple_connect_db(self):
        """ Create a connection pool using the database URL """
        if self.dburl:
            return psycopg2.pool.SimpleConnectionPool(1, 10, self.dburl)
        else:
            return psycopg2.pool.SimpleConnectionPool(1, 10, user=self.user,
                                                      password=self.password,
                                                      host=self.host,
                                                      port=self.port,
                                                      database=self.dbname)

    def put_db_connection(self, conn):
        conn = conn or self.connect_db()
        self.putconn(conn)

    def get_db_connection(self):
        return self.connect_db()

    def get_insert(self, tableName):
        return self.table_mgr.get_insert(tableName)

    def fetchFromDb(self, tableName, searchValue):
        return self.table_mgr.fetchFromDb(tableName, searchValue, self.connect_db())

    def insertIntoDb(self, tableName, searchValue, insertValue):
        return self.table_mgr.insert_intoDb(tableName, searchValue, insertValue, self.connect_db())

    def search_multiple_fields(self, query, **kwargs):
        return self.table_mgr.search_multiple_fields(query=query, conn=self.connect_db())

    def get_first_row_as_dict(self, tableName=None, rowNum=1):
        return self.table_mgr.get_first_row_as_dict(tableName=tableName, rowNum=rowNum, conn=self.connect_db())
