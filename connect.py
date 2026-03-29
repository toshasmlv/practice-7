import psycopg2
from config import load_config


def connect(config=None):
    """
    Connect to the PostgreSQL database server.
    Returns a psycopg2 connection object, or None on failure.
    """
    if config is None:
        config = load_config()
    try:
        conn = psycopg2.connect(**config)
        print('Connected to the PostgreSQL server.')
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f'Connection error: {error}')
        return None


if __name__ == '__main__':
    conn = connect()
    if conn:
        print(f'PostgreSQL version: {conn.server_version}')
        conn.close()