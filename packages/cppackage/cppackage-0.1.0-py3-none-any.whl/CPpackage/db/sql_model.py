import pymysql
import time
from pymysql import Error
from .config import get_db_config

def _get_connection(database=None, port=None):
    cfg = get_db_config()
    db = database if database is not None else cfg.get('database')
    prt = port if port is not None else cfg.get('port', 3306)
    return pymysql.connect(
        host=cfg.get('host'),
        user=cfg.get('user'),
        password=cfg.get('password'),
        database=db,
        port=prt,
    )

def sel_data(sql, port=None, database=None):
    try:
        conn = _get_connection(database=database, port=port)
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except pymysql.MySQLError as e:
        print(f"An error occurred: {e}")

def update_data(sql, values, port=None, database=None):
    conn = _get_connection(database=database, port=port)
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()

def updata(data, databases, table):
    s = ""
    st1 = ""
    for i in data.columns.values:
        s = s + "`" + i + "`,"
        st1 = st1 + "%s,"
    s = s[:-1]
    st1 = st1[:-1]
    all_data = []
    for _, k in data.iterrows():
        all_data.append(tuple(k.to_list()))
    sql = 'INSERT INTO %s (%s) VALUES (%s)' % (table, s, st1)
    update_datas(sql, tuple(all_data), database=databases)
    time.sleep(2)

def deldata(all_del_list, id_name, table_name, database):
    str11 = ""
    for te in all_del_list:
        if "str" in str(type(te)):
            str11 = str11 + "'" + str(te) + "',"
        else:
            str11 = str11 + str(te) + ","
    str11 = str11[:-1]
    delsql = 'DELETE from `%s` where %s in (%s)' % (table_name, id_name, str11)
    del_data(delsql, database=database)

def deldata_time(id_name, table_name, id, database, time_name, start_time, end_time):
    delsql = 'DELETE from `%s` where %s = %s and `%s`>= "%s" and  `%s`<= "%s"' % (
        table_name, id_name, id, time_name, start_time, time_name, end_time
    )
    del_data(delsql, database=database)

def update_datas(sql, values, port=None, database=None):
    with _get_connection(database=database, port=port) as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, values)
            conn.commit()

def del_data(sql, port=None, database=None):
    try:
        conn = _get_connection(database=database, port=port)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
    except pymysql.MySQLError as e:
        print(f"An error occurred: {e}")

def update_test(df, table_name, databases):
    try:
        conn = _get_connection(database=databases)
        cursor = conn.cursor()
        columns = ', '.join(df.columns)
        values_template = ', '.join([f'({", ".join(["%s"] * len(df.columns))})'] * len(df))
        update_clause = ', '.join([f'{col} = VALUES({col})' for col in df.columns if col != 'id'])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES {values_template} " \
                  f"ON DUPLICATE KEY UPDATE {update_clause}"
        values = [tuple(row) for row in df.values]
        flat_values = [item for sublist in values for item in sublist]
        cursor.execute(sql, flat_values)
        conn.commit()
        print(f"成功插入/更新 {cursor.rowcount} 条记录")
    except Error as e:
        print(f"数据库错误: {e}")
    finally:
        if conn:
            conn.close()
