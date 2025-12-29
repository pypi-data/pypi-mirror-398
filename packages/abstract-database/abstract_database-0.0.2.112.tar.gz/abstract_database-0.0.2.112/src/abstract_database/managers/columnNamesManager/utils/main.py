from ..imports import *
class columnNamesManager(metaclass=SingletonMeta):
    def __init__(self):
        if not hasattr(self, 'initialized'):  
            self.initialized = True
            self.columnNames = {}

    def get_column_names(self, tableName, schema='public'):
        if tableName not in self.columnNames:
            self.columnNames[tableName] = self.fetch_column_names(tableName, schema)
        return self.columnNames[tableName]

    def fetch_column_names(self, tableName, schema='public'):
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position;
        """
        results = query_data(query, [tableName, schema], error='Error fetching column names',zipRows=False)
        if results:
            return [row[0] for row in results]
        logger.warning(f"No columns found for table {tableName} in schema {schema}")
    def zip_rows(self, tableName, rows, schema='public'):
        column_names = self.get_column_names(tableName, schema)
        if rows:
            return [dict(zip(columnNames,make_list(row))) for row in rows]
