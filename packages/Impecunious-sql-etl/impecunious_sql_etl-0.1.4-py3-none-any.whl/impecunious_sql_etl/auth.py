import logging
from sqlalchemy import create_engine
from urllib.parse import quote_plus

def create_sql_server_engine(server, database, auth_mode="sql",
                             username=None, password=None,
                             driver="ODBC Driver 18 for SQL Server"):
    logging.info(f"Connecting to SQL Server: {server} | Database: {database} | Auth: {auth_mode}") # Added logging
    try:
        if auth_mode == "sql":
            conn = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;"
        else:
            conn = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Authentication=ActiveDirectoryInteractive;Encrypt=yes;"

        engine = create_engine(
            f"mssql+pyodbc:///?odbc_connect={quote_plus(conn)}",
            fast_executemany=True
        )
        return engine
    except Exception as e:
        logging.error(f"Failed to create engine for {server}: {e}")
        raise
