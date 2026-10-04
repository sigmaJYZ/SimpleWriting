sqlpipe 是一个命令行工具，可以把 Postgres 表同步到 S3，并保存为 Parquet（一种列式文件格式）文件。你只需指定源表和目标存储桶，sqlpipe 就会读取表中的数据，写出 Parquet 文件，再上传到 S3。

Parquet 文件体积小，读取快。Athena、Spark、DuckDB 等分析工具可以直接查询这些文件。因此你不必在生产数据库上运行重型分析查询。sqlpipe 适合用来做数据备份、数据湖导入和定期的数据导出。