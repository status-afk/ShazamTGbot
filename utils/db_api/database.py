import sqlite3
from datetime import datetime


def logger(statement):
    print(f"""
    _______________________________________
    Executing:
    {statement}
    _______________________________________
    """)


class Database:
    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        data = None
        try:
            cursor.execute(sql, parameters)
            if commit:
                connection.commit()
            if fetchall:
                data=cursor.fetchall()
            if fetchone:
                data=cursor.fetchone()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        finally:
            connection.close()
        return data
    @staticmethod
    def format_args(sql,parameters:dict):
        sql+="AND".join([f"{item} = ?" for item in parameters])
        return sql,tuple(parameters.values())