from django.db import connection


def fetchone(query: str, params=None, desc=True):
    if params is None:
        params = []
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchone()
        if not desc or not rows:
            return rows
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, rows))

def fetchall(query: str, params=None, desc=True):
    if params is None:
        params = []
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not desc:
            return rows
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
