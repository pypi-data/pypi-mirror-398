import os

_db_config = {
    'host': os.getenv('CPPACKAGE_DB_HOST'),
    'user': os.getenv('CPPACKAGE_DB_USER'),
    'password': os.getenv('CPPACKAGE_DB_PASSWORD'),
    'database': os.getenv('CPPACKAGE_DB_NAME'),
    'port': int(os.getenv('CPPACKAGE_DB_PORT', '3306')),
}

def set_db_config(host=None, user=None, password=None, database=None, port=None):
    if host is not None:
        _db_config['host'] = host
    if user is not None:
        _db_config['user'] = user
    if password is not None:
        _db_config['password'] = password
    if database is not None:
        _db_config['database'] = database
    if port is not None:
        _db_config['port'] = int(port)

def get_db_config():
    return _db_config.copy()
