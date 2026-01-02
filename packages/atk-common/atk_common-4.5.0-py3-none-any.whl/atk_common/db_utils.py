def sql(connection, sql, get_one):
    from psycopg2.extras import RealDictCursor
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql)
            if get_one:
                return cursor.fetchone()
            return cursor.fetchall()

def sql_with_record(connection, sql, record):
    from psycopg2.extras import RealDictCursor
    with connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, record)
            return cursor.fetchone()

def convert_none_to_null(value):
    if value is None or value == '':
        return 'null'
    if type(value) is str:
        return '\'' + value + '\''
    return value

def date_time_utc_column(column):
    return 'TO_CHAR({0} at time zone \'UTC\', \'yyyy-mm-dd hh24:mi:ss.ms"Z"\')'.format(column)
