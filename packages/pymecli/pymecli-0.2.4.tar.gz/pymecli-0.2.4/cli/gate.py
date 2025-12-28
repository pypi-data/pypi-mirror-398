import typer

from crypto.gate import gate_close, gate_open
from utils.mysql import get_database_engine

app = typer.Typer()


@app.command()
def sync(
    env_path: str = "d:/.env", csv_path: str = "d:/github/meme2046/data/gate_0.csv"
):
    """同步mysql中grid数据到csv文件"""
    engine = get_database_engine(env_path)
    gate_open(engine, csv_path)
    gate_close(engine, csv_path)
