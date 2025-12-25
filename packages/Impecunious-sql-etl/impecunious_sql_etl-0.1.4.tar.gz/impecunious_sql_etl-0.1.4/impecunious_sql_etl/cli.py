import os, click, logging, glob
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
    cfg = load_config(config)
    tgt_engine = create_sql_server_engine(**cfg["target"]["connection"])
    schema = cfg["target"].get("schema", "dbo")

    expanded_sources = []
    for src in cfg["sources"]:
        path = src.get("path")

        # Check if the path is a directory
        if path and os.path.isdir(path):
            logging.info(f"Scanning directory: {path}")
            # Find all csv and parquet files in the folder
            files = glob.glob(os.path.join(path, "*.csv")) + glob.glob(os.path.join(path, "*.parquet"))

            for f in files:
                # Create a new source object for each file found, inheriting defaults from the dir config
                new_src = src.copy()
                new_src["path"] = f
                new_src["type"] = "csv" if f.endswith(".csv") else "parquet"
                expanded_sources.append(new_src)
        else:
            expanded_sources.append(src)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_source, s, tgt_engine, schema): s for s in expanded_sources}
        for f in as_completed(futures):
            f.result()

if __name__ == "__main__":
    run() # FIXED: Added entry point to trigger the click command
