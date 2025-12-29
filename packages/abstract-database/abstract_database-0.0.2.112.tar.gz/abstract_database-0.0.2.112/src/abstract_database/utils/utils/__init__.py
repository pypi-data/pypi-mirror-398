from ..imports import *
from .config_utils import *
from .db_functions import *
from .get_tables import *
from .get_templates import *
from .get_time_data import *
from .image_utils import *
from .legacy_utils import *
from .solana import *
def select_one(query, *args):
    rows = select_rows(query, *args)
    return get_rows(rows)
