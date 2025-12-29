from .databaseManager import *
def ensure_db_manager(db_mgr=None, conn_mgr=None,**kwargs):
    return db_mgr or DatabaseManager(conn_mgr=conn_mgr,**kwargs)
