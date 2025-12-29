# -*- coding: utf-8 -*-
import pandas as pd
from sqlalchemy import create_engine


class PdMySQL:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)

    def fetch_all(self, sql, *args):
        """
        Execute a query and return all results as a DataFrame.

        :param sql: SQL query statement
        :param args: list of parameters
        :return: DataFrame
        """
        df = pd.read_sql(sql, con=self.engine, params=args if args else None)
        return df

    def fetch_one(self, sql, *args):
        """
        Fetch a single record from the database.

        :param sql: SQL query statement
        :param args: list of parameters
        :return: Single record or None if no result is found
        """
        df = self.fetch_all(sql, *args)
        return df.iloc[0] if not df.empty else None

    def execute_sql(self, sql, *args):
        """
        Execute an SQL statement.

        :param sql: SQL execution statement
        :param args: list of parameters
        :return: Number of affected rows
        """
        with self.engine.connect() as connection:
            result = connection.execute(sql, *args)
            return result.rowcount

    def database_name(self):
        """
        Get the current database name.

        :return: Database name
        """
        return self.engine.url.database
