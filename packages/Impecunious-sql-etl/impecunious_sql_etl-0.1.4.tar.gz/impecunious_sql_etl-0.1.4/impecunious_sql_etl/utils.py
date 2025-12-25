import os
def infer_table_name(src):
    return os.path.splitext(os.path.basename(src["path"]))[0]
