from abstract_utilities import make_list,SingletonMeta,get_logFile
from ....query_utils.utils.query_utils.utils import query_data,get_all_table_names
from psycopg2 import sql, connect
logger = get_logFile('query_utils')
