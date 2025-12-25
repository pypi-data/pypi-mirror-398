def transform(df, mapping=None, dtypes=None, select=None):
    if mapping: df = df.rename(columns=mapping)
    if select: df = df[select]
    if dtypes:
        for c, t in dtypes.items():
            df[c] = df[c].astype(t)
    return df
