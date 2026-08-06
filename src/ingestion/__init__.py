"""
Glue ETL jobs for structured INEC price data.

Two sources, both published monthly by Ecuador's Instituto Nacional de
Estadística y Censos (INEC):
  - IPC (Índice de Precios al Consumidor): the consumer price index itself,
    by division/group/class/subclass/product hierarchy
  - Canasta Familiar Básica / Vital: the cost of the basic/vital household
    basket, by city and region

Both jobs write normalized Parquet to the processed data S3 bucket,
partitioned by source and year/month, and register/update the corresponding
Glue Data Catalog table so Athena can query it directly.
"""
