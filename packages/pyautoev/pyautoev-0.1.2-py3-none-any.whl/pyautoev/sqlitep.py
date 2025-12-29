# -*- coding: utf-8 -*-
import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd


def insert_(sqlite_path, df, table_name):
    """
    Insert a DataFrame into a SQLite database table.

    :param sqlite_path: Path to the SQLite database file or `:memory:`
    :param df: Pandas DataFrame to be inserted
    :param table_name: Target table name
    :return: Status message string
    """
    SUCCESS_MESSAGE = 'Data inserted successfully'
    EMPTY_DF_MESSAGE = "{} is empty"
    ERROR_MESSAGE = "Error inserting data: {}"
    INVALID_INPUT_MESSAGE = "Invalid input: {}"

    # Input validation
    if not isinstance(sqlite_path, str) or sqlite_path.strip() == "":
        return INVALID_INPUT_MESSAGE.format("sqlite_path is invalid")
    if not isinstance(table_name, str) or table_name.strip() == "":
        return INVALID_INPUT_MESSAGE.format("table_name is invalid")
    if not isinstance(df, pd.DataFrame):
        return INVALID_INPUT_MESSAGE.format("df is invalid")

    try:
        # Check for empty DataFrame
        if df.empty:
            return EMPTY_DF_MESSAGE.format(table_name)

        # Create engine and prepare connection
        engine = create_engine(f'sqlite:///{sqlite_path}', echo=False)

        # Dynamic chunksize calculation
        chunksize = max(1, len(df) // 10)

        # Perform bulk insert
        with engine.begin() as connection:
            df.to_sql(
                table_name,
                con=connection,
                if_exists='append',
                index=False,
                chunksize=chunksize,
                method='multi'
            )

        return SUCCESS_MESSAGE

    except SQLAlchemyError as e:
        return ERROR_MESSAGE.format(f"SQLAlchemy error occurred: {str(e)}")
    except Exception as e:
        return ERROR_MESSAGE.format(f"An unexpected error occurred: {str(e)}")
    finally:
        if 'engine' in locals():
            engine.dispose()


def delete_(sqlite_path, table_name, condition=None):
    """
    Delete records from a SQLite table based on an optional WHERE clause.

    :param sqlite_path: Path to the SQLite database file or `:memory:`
    :param table_name: Table name to delete from
    :param condition: Optional WHERE condition (basic format only)
    :return: Dictionary with status and message
    """
    try:
        # Validate SQLite database path
        if not os.path.isfile(sqlite_path) and sqlite_path != ":memory:":
            return {"status": "error", "message": f"SQLite database file does not exist: {sqlite_path}"}

        # Create engine
        engine = create_engine(f'sqlite:///{sqlite_path}', echo=False)

        with engine.connect() as connection:
            # Build DELETE statement safely
            if condition:
                if not isinstance(condition, str) or ";" in condition:
                    return {"status": "error", "message": "Invalid condition provided"}
                delete_statement = text(f"DELETE FROM {table_name} WHERE {condition}")
            else:
                delete_statement = text(f"DELETE FROM {table_name}")

            # Execute deletion
            result = connection.execute(delete_statement)

        return {"status": "success", "message": f"{result.rowcount} rows deleted successfully"}

    except FileNotFoundError:
        return {"status": "error", "message": f"Database file not found: {sqlite_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting data: {e}"}
    finally:
        if 'engine' in locals():
            engine.dispose()
