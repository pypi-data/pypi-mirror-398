import logging
from sqlalchemy import text, inspect

def load(df, engine, table, schema="dbo", mode="truncate_load"):
    row_count = len(df)
    logging.info(f"Loading {row_count} rows into {schema}.{table} using mode: {mode}")

    try:
        # Use a single transaction block
        with engine.begin() as conn:
            inspector = inspect(engine)
            table_exists = inspector.has_table(table, schema=schema)

            if mode == "truncate_load":
                if table_exists:
                    logging.info(f"Table {schema}.{table} exists. Truncating existing data...")
                    conn.execute(text(f"TRUNCATE TABLE {schema}.{table}"))
                else:
                    logging.info(f"Table {schema}.{table} does not exist. It will be created.")

                # 'append' mode in pandas creates the table if it is missing
                df.to_sql(table, conn, schema=schema, if_exists="append", index=False)

            elif mode == "drop_recreate":
                logging.info(f"Dropping and recreating {schema}.{table}...")
                df.to_sql(table, conn, schema=schema, if_exists="replace", index=False)

            elif mode == "append":
                if not table_exists:
                    logging.info(f"Table {schema}.{table} does not exist. Creating it...")
                df.to_sql(table, conn, schema=schema, if_exists="append", index=False)

        logging.info(f"Successfully loaded {table}")

    except Exception as e:
        logging.error(f"Load failed for {table}: {e}")
        raise
