from ..imports import get_file_parts,connectionManager
def get_db_name(dbName=None, dbPath=None, dbUrl=None):
    if dbName:
        return dbName
    fileParts_js = get_file_parts(dbPath or dbUrl)
    return fileParts_js.get("fileName")

def get_db_url(dbPath=None):
    return connectionManager().dburl

def get_db_engine(dbUrl=None, dbPath=None):
    if dbUrl is None:
        if dbPath is None:
            return
        dbUrl = get_db_url(dbPath)
    return create_engine(dbUrl)
