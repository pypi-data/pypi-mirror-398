import os, click, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from impecunious_sql_etl.config import load_config
from impecunious_sql_etl.etl_log import setup_logging
from impecunious_sql_etl.auth import create_sql_server_engine
from impecunious_sql_etl.extract import extract
from impecunious_sql_etl.transform import transform
from impecunious_sql_etl.load import load
from impecunious_sql_etl.utils import infer_table_name


def process_source(src, tgt_engine, schema):
    try:
        table = src.get("target_table") or infer_table_name(src)
        logging.info(f"--- Starting Process: {table} ---")

        if src["type"] == "sql":
            src["engine"] = create_sql_server_engine(**src["connection"])

        df = extract(src)
        df = transform(df, src.get("mapping"), src.get("dtypes"), src.get("select"))

        if src.get("save_parquet"):
            os.makedirs("parquet_exports", exist_ok=True)
            df.to_parquet(f"parquet_exports/{table}.parquet", index=False)
            logging.info(f"Saved local parquet for {table}")

        load(df, tgt_engine, table, schema, src.get("mode","truncate_load"))
        logging.info(f"--- Finished Process: {table} ---")
    except Exception as e:
        logging.error(f"Critical error processing source {src.get('path')}: {e}")

@click.command()
@click.option("--config", required=True)
@click.option("--workers", default=4, show_default=True)
def run(config, workers):
    setup_logging()
    logging.info(f"Starting ETL Job with config: {config}")

    try:
        cfg = load_config(config)
        tgt_engine = create_sql_server_engine(**cfg["target"]["connection"])
        schema = cfg["target"].get("schema","dbo")

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(process_source, s, tgt_engine, schema): s for s in cfg["sources"]}
            for f in as_completed(futures):
                f.result() # This will surface exceptions if not caught in process_source

    except Exception as e:
        logging.critical(f"ETL Job failed: {e}")

if __name__ == "__main__":
    run() # FIXED: Added entry point to trigger the click command
