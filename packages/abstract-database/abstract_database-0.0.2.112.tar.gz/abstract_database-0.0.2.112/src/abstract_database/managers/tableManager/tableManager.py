from .utils import *
class TableManager(metaclass=SingletonMeta):
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.insert_list = []
            self.dbNames=[]
            self.env_path = None
    def add_insert_list(self,conn,tables,dbName):
        self.dbNames.append(dbName)
        setup_database(tables,conn)
        self.insert_list+=tables
    def get_insert(self, tableName):
        tableName = tableName.lower()
        insertList = [ls for ls in self.insert_list if ls.get("tableName") == tableName.lower()]
        return insertList[0] if insertList else None

    def fetchFromDb(self,tableName,searchValue,conn):
        cached_response = fetchFromDb(self.get_insert(tableName), searchValue, conn)
        if cached_response:
            return cached_response

    def insert_intoDb(self,tableName,searchValue,insertValue,conn):
        return insert_intoDb(self.get_insert(tableName), searchValue,insertValue,conn )
    def search_multiple_fields(self, query,conn,**kwargs):
        return search_multiple_fields(query,conn)
    def get_first_row_as_dict(self,tableName=None,conn=None,rowNum=None):
        """Fetch the first row of data from the specified table and return as a dictionary."""
        rowNum= rowNum or 1
        query = f"SELECT * FROM {tableName} ORDER BY id ASC LIMIT {rowNum};"
        cur = conn.cursor()
        try:
            cur.execute(query)
            first_row = cur.fetchone()
            col_names = [desc[0] for desc in cur.description]
            if first_row:
                return dict(zip(col_names, first_row))
            return None
        except psycopg2.Error as e:
            print(f"Error fetching the first row: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    def add_table_config(self,dbName,dbType):
        table_config = safe_read_from_json(get_table_path(dbName,dbType))
        self.insert_list+=table_config
    def add_unique_header(self,uniqueHeader,tableName,dbName,dbType):
        table_path = get_table_path(dbName,dbType)
        insertTables = safe_read_from_json(get_table_path(dbName,dbType))
        newTables = []
        tableName = tableName.lower()
        for i,insertTable in enumerate(insertTables):
            if tableName == insertTable.get('tableName'):
                if 'excelUniqueHeaders' not in insertTable:
                    insertTable['excelUniqueHeaders'] = []
                if uniqueHeader not in insertTable['excelUniqueHeaders']:
                    insertTable['excelUniqueHeaders'].append(uniqueHeader)
                    self.insert_list = [insertTable if table.get('tableName') == tableName else table for table in self.insert_list]
            newTables.append(insertTable)
        safe_dump_to_file(data=newTables,file_path=table_path)
