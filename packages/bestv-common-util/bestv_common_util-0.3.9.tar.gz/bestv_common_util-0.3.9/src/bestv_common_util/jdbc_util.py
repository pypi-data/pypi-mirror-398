import logging


def parse_jdbc_url(jdbc_url):
    from urllib.parse import urlparse, parse_qs

    """
    解析 MySQL JDBC URL 并返回 PyMySQL 连接所需的参数
    支持格式：
      1. jdbc:mysql://user:pass@host:port/database
      2. jdbc:mysql://host:port/database?user=xxx&password=xxx
    """
    if not (jdbc_url.startswith("jdbc:") or jdbc_url.startswith("mysql+")):
        raise ValueError("Invalid JDBC URL: Must start with 'jdbc:' or 'mysql+'")

    # 去掉 jdbc: 前缀并解析
    parsed = urlparse(jdbc_url[5:])  # 移除 "jdbc:"

    # 验证必要参数
    if not parsed.hostname:
        raise ValueError("Invalid JDBC URL: Host not found")

    # 提取基础参数
    host = parsed.hostname
    port = parsed.port or 3306  # 默认端口 3306
    database = parsed.path[1:] if parsed.path else None  # 移除开头的 '/'

    # 优先使用 URL 中的用户认证 (user:pass@host)
    user = parsed.username
    password = parsed.password

    # 次优使用查询参数 (?user=xx&password=xx)
    query_params = parse_qs(parsed.query)
    if user is None and "user" in query_params:
        user = query_params["user"][0]
    if password is None and "password" in query_params:
        password = query_params["password"][0]

    return {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password
    }


def pandas_upsert_to_postgres(engine, df, schema, table_name, conflict_columns):
    """
    使用 Pandas 在 PostgreSQL 中执行 Upsert 操作

    参数:
        df: 要插入/更新的 DataFrame
        table_name: 目标表名
        conflict_columns: 用于检测冲突的列名列表
        engine: SQLAlchemy 引擎对象
    """
    from sqlalchemy import text, inspect
    from sqlalchemy.exc import SQLAlchemyError
    try:
        # 创建临时表名
        temp_table = f"{table_name}_temp"
        inspector = inspect(engine)
        if not inspector.has_table(temp_table, schema=schema):
            with engine.connect() as conn:
                # 不生效
                # conn.execute(f"CALL hg_create_table_like('{schema}.{temp_table}', 'select * from {schema}.{table_name}');")
                conn.execute(f"create table {schema}.{temp_table} as select * from {schema}.{table_name} where false")
        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {schema}.{temp_table}"))

        # 将数据写入临时表
        df.to_sql(
            name=temp_table,
            schema=schema,
            con=engine,
            if_exists='append',
            index=False
        )

        # 获取所有列名
        columns = ', '.join(df.columns)
        conflict_columns_str = ', '.join(conflict_columns)

        # 创建 SET 子句（排除冲突列）
        set_clause = ', '.join(
            [f"{col} = EXCLUDED.{col}"
             for col in df.columns
             if col not in conflict_columns]
        )

        # 构建 UPSERT 语句
        upsert_query = f"""
            INSERT INTO {schema}.{table_name} ({columns})
            SELECT {columns} FROM {schema}.{temp_table}
            ON CONFLICT ({conflict_columns_str}) 
            DO UPDATE SET {set_clause}
        """

        # 执行 UPSERT
        with engine.connect() as conn:
            conn.execute(text(upsert_query))

        logging.info("execute success upsert tablename=%s.%s, rows=%s", schema, table_name,  len(df))

    except SQLAlchemyError as e:
        logging.error(e)
        raise
    finally:
        logging.info("clear temp table: %s.%s", schema, temp_table)
        # 清理临时表
        try:
            with engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE {schema}.{temp_table}"))
        except Exception as e:
            logging.error("clear temp tablename=%s.%s error: %s", schema, temp_table, e)