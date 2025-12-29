from ..imports import *
from ...query_utils.utils import query_data
# Environment setup
ENV_PATH = '/home/solcatcher/.env'

def get_env_val(key, default=None):
    """Retrieve environment variable with optional default."""
    return get_env_value(key=key, path=ENV_PATH) or default
def manual_connecty():
    # Centralized configuration
    CONFIG = {
        'RABBITMQ': {
            'HOST': get_env_val("SOLCATCHER_AMQP_HOST", 'local'),
            'PORT': get_env_val("SOLCATCHER_AMQP_PORT", '5672'),
            'USER': get_env_val("SOLCATCHER_AMQP_USER", 'solcatcher'),
            'NAME': get_env_val("SOLCATCHER_AMQP_NAME", 'solcatcher'),
            'PASSWORD': get_env_val("SOLCATCHER_AMQP_PASSWORD", 'solcatcher123'),
        },
        'POSTGRESQL': {
            'HOST': get_env_val("SOLCATCHER_POSTGRESQL_HOST", 'solcatcher.io'),
            'PORT': get_env_val("SOLCATCHER_POSTGRESQL_PORT", '5432'),
            'USER': get_env_val("SOLCATCHER_POSTGRESQL_USER", 'solcatcher'),
            'NAME': get_env_val("SOLCATCHER_POSTGRESQL_NAME", 'solcatcher'),
            'PASSWORD': get_env_val("SOLCATCHER_POSTGRESQL_PASSWORD", 'solcatcher123!!!456'),
        }
    }

    DB_URL = (
        f"postgresql://{CONFIG['POSTGRESQL']['USER']}:{CONFIG['POSTGRESQL']['PASSWORD']}"
        f"@{CONFIG['POSTGRESQL']['HOST']}:{CONFIG['POSTGRESQL']['PORT']}/{CONFIG['POSTGRESQL']['NAME']}"
    )

    def get_connection():
        """Establish a PostgreSQL connection."""
        return psycopg2.connect(
            dbname=CONFIG['POSTGRESQL']['NAME'],
            user=CONFIG['POSTGRESQL']['USER'],
            password=CONFIG['POSTGRESQL']['PASSWORD'],
            host=CONFIG['POSTGRESQL']['HOST'],
            port=CONFIG['POSTGRESQL']['PORT']
        )
