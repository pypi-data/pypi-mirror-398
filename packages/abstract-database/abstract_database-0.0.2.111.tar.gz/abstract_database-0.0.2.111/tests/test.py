from imports import *
POSTGRES_DSN = {
    "dbname":"ae_clients_db",
    "user":"ae_ext_rw",

}
conn_mgr = get_db_connection(**POSTGRES_DSN)

