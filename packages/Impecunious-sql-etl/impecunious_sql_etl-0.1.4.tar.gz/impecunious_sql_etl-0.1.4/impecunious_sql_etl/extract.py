import pandas as pd
import logging

def extract(source):
    t, p = source["type"], source["path"]
    logging.info(f"Extracting from {t.upper()}: {p}") # Added logging
    try:
        if t == "csv": return pd.read_csv(p)
        if t == "json": return pd.read_json(p, lines=True)
        if t == "parquet": return pd.read_parquet(p)
        if t == "sql": return pd.read_sql(p, source["engine"])
        raise ValueError(f"Unsupported source type: {t}")
    except Exception as e:
        logging.error(f"Extraction failed for {p}: {e}")
        raise
