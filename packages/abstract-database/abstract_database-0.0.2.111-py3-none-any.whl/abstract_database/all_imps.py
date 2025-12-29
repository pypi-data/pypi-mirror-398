import logging,os,yaml,io,requests,time,json,warnings,traceback,json,asyncio,asyncpg,psycopg2
from abstract_math import divide_it
from abstract_utilities import flatten_json,safe_read_from_json,get_any_value,is_number,safe_dump_to_file,make_list,SingletonMeta,get_logFile,initialize_call_log
from abstract_solcatcher_database import *
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from PIL import Image
from abstract_apis import getRequest,get_response,asyncPostRpcRequest, asyncPostRequest
from abstract_security import get_env_value
from psycopg2.extras import Json
from psycopg2 import sql, connect
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from psycopg2.extras import RealDictCursor
from abstract_pandas import safe_excel_save
logging.basicConfig()
from abstract_utilities import *
all_imps = []
def get_all_real_imps(file):
    contents = read_from_file(file)
    lines = contents.split('\n')
    for line in lines:
        if line.startswith('from '):
            from_line = line.split('from ')[-1]
            dot_fro = ""
            dirname = file
            for char in from_line:
                if  char != '.':
                    line = f"from {dot_fro}{eatAll(from_line,'.')}"
                    if line in all_imps:
                        line = ""
                    break
                if dot_fro == "":
                    dot_fro = ""
                dirname = os.path.dirname(dirname)
                dirbase = os.path.basename(dirname)
                dot_fro = f"{dirbase}.{dot_fro}"
        if line:
            all_imps.append(line)
            print(line)
    return all_imps
files = get_files_and_dirs(get_caller_dir(),allowed_exts=['.py'])[-1]
files = [get_all_real_imps(f) for f in files if f and f.endswith('imports.py')]
from fetch_utils.imports import logging,psycopg2,traceback,warnings,RealDictCursor,sql,get_env_value,get_logFile,make_list
from fetch_utils.managers.columnNamesManager.utils.main import columnNamesManager,query_data,get_all_table_names
from fetch_utils.managers.connectionManager.utils import connectionManager,get_cur_conn
from managers.imports import *
from managers.tableManager.imports import json,asyncio,asyncpg,psycopg2,asyncPostRpcRequest, asyncPostRequest
from abstract_security import *
from abstract_utilities import is_number, SingletonMeta, safe_read_from_json
from abstract_utilities import safe_read_from_json
from managers.connectionManager.imports.tableManager import *
import psycopg2
from psycopg2 import pool
from managers.envManager.connectionManager import*
from managers.envManager.imports import safe_read_from_json,SingletonMeta, json,os
from typing import *
from abstract_utilities import SingletonMeta
from managers.dbManager.connectionManager import connectionManager
from abstract_utilities import make_list,SingletonMeta,get_logFile
from managers.columnNamesManager.imports.query_utils.utils.query_utils.utils import query_data,get_all_table_names
logger = get_logFile('query_utils')
from managers.databaseManager.imports import pd,psycopg2,flatten_json,safe_excel_save
from managers.databaseManager.connectionManager import *
from sqlalchemy import Boolean, create_engine, String, BigInteger, JSON, Text, cast, Index, MetaData, Table, text, inspect, Column, Integer, Float
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base
from abstract_utilities import SingletonMeta,get_file_parts,flatten_json
from abstract_utilities.cmd_utils.user_utils import *
from managers.databaseBrowser.imports.connectionManager import connectionManager
from utils.imports import *
from utils.utils.imports import *
from utils.db_functions.get_tables import *
from utils.db_functions.imports import Json,text,SQLAlchemyError
from utils.legacy_utils.imports import (
    datetime,
    timedelta,
    np,
    pd
    )
from utils.config_utils.imports import make_list,time
from utils.image_utils.imports import logging,io,requests,Image,getRequest,get_response
logging.basicConfig(level=logging.ERROR)
from utils.get_templates.imports import is_number,safe_dump_to_file,json
from utils.get_time_data.imports import time,datetime, timedelta,pd,np
from utils.solana.imports import (
    os,
    get_meta_data_from_meta_id,
    asyncio,
    async_call_solcatcher_ts,
    get_meta_data_from_meta_id,
    asyncio,
    async_call_solcatcher_ts,
    logging,
    divide_it,
    get_any_value
    
    )
from utils.get_tables.imports import get_env_value
from query_utils.imports import *
from query_utils.utils.imports import *
from utils.query_utils.imports import (make_list,
                                SingletonMeta,
                                get_logFile,
                                psycopg2,
                                RealDictCursor,
                                initialize_call_log,
                                make_list,
                                SingletonMeta,
                                sql,
                                connect,
                                get_env_value,
                                traceback,
                                warnings
                                )
logger = get_logFile('fetch_utils')
from utils.manual_connect.imports import sql, connect,make_list,SingletonMeta
