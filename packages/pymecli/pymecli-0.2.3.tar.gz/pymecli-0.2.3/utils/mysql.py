import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text

from utils.pd import deduplicated


def get_database_engine(env_path: str) -> Engine:
    """创建数据库引擎"""
    load_dotenv(env_path)
    host = os.getenv("UNI_CLI_MYSQL_HOST")
    port = os.getenv("UNI_CLI_MYSQL_PORT")
    user = os.getenv("UNI_CLI_MYSQL_USER")
    password = os.getenv("UNI_CLI_MYSQL_PASSWORD")
    database = os.getenv("UNI_CLI_MYSQL_DATABASE")

    engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        raise

    return engine


def mysql_to_csv(
    engine: Engine,
    csv_path: str,
    table: str,
    query: str,
    update_status: int,
    d_column_names: list[str],
    pd_dtype: dict | None = None,
    del_column_names: list[str] = ["id"],
) -> int:
    # 查询数据
    data_frame = pd.read_sql(query, engine, dtype=pd_dtype)
    # 提取 'id' 列
    ids = data_frame["id"].tolist()
    # 删除 'id' 列
    data_frame = data_frame.drop(columns=del_column_names)

    # 根据 'open_at' 列降序排序
    # data_frame = data_frame.sort_values(by="open_at", ascending=False)

    # 将数据追加写入 CSV 文件
    data_frame.to_csv(
        csv_path,
        mode="a",
        header=not os.path.exists(csv_path),
        index=False,
        encoding="utf-8",
    )
    # csv去重,保留最后加入的数据
    deduplicated(csv_path, d_column_names, "last", pd_dtype)

    # 根据提取的 'id' 列更新数据库中 up_status 字段
    if ids:
        # 使用 text() 构建查询时，确保 :ids 是一个列表
        update_query = text(
            f"UPDATE {table} SET up_status = :status WHERE id IN ({','.join(map(str, ids))});"
        )
        with engine.connect() as connection:
            with connection.begin():
                result = connection.execute(
                    update_query,
                    {"status": update_status},
                )

                return result.rowcount

    return 0
