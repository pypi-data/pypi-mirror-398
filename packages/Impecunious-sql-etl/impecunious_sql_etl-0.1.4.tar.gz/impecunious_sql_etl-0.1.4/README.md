# Impecunious SQL ETL

Config-driven, parallel ETL tool for SQL Server with Azure AD and SQL authentication.

## Install
pip install Impecunious-sql-etl

## Run
impecunious-sql-etl --config configs/etl.yaml --workers 4

## Defaults
| Config Item    | If Missing | Default Used                                            |
| -------------- | ---------- | ------------------------------------------------------- |
| `target_table` | omitted    | **Inferred automatically** from file name or SQL source |
| `mapping`      | omitted    | **No renaming** (1:1 columns)                           |
| `dtypes`       | omitted    | **Pandas inferred types**                               |
| `select`       | omitted    | **All columns loaded**                                  |
| `mode`         | omitted    | `truncate_load`                                         |
| `schema`       | omitted    | `dbo`                                                   |

## Minimal config example
```yaml
target:
  connection:
    server: myserver.database.windows.net
    database: TargetDB
    auth_mode: azure_interactive

sources:
  - type: csv
    path: data/customers.csv
```
## Multiple files + SQL table config example
```yaml
target:
  connection:
    server: myserver.database.windows.net
    database: TargetDB
    auth_mode: azure_interactive

sources:
  - type: csv
    path: data/customers.csv

  - type: parquet
    path: data/products.parquet

  - type: sql
    path: SELECT * FROM sales.orders
    connection:
      server: onprem-sql
      database: SourceDB
      auth_mode: sql
      username: etl_user
      password: secret
    mode: append
    save_parquet: true
```



