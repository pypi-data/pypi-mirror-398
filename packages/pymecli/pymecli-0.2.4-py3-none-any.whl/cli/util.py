import platform
import secrets
import string
import sys
import uuid as u
from datetime import datetime

import arrow
import pytz
import typer
from babel.dates import format_datetime
from cowsay.__main__ import cli

app = typer.Typer()


@app.command()
def sid(
    length: int = typer.Argument(30, help="生成secure_id的长度"),
):
    chars = string.ascii_letters + string.digits
    id = "".join(secrets.choice(chars) for _ in range(length))
    print(id)


@app.command()
def uuid():
    print(u.uuid4())


@app.command()
def os():
    print(platform.system())


@app.command()
def ts():
    timestamp = arrow.now().timestamp()
    print(int(timestamp))


@app.command()
def ms():
    timestamp = arrow.now().timestamp()
    print(int(timestamp * 1000))


@app.command()
def v():
    print(f"🧊 python:{sys.version}")


def strf_time(zone: str):
    tz = pytz.timezone(zone)
    now = datetime.now(tz)
    # locale="zh_CN" 会使月份和星期的名称显示为中文
    # locale="en_US" 则会显示为英文
    return format_datetime(
        now, "yyyy年MM月dd日 HH:mm:ss EEEE ZZZZ zzzz", locale="zh_CN"
    )


@app.command()
def st():
    t0 = strf_time("UTC")
    t1 = strf_time("America/New_York")
    t2 = strf_time("Asia/Shanghai")

    print(t0)
    print(t1)
    print(t2)


@app.command()
def stoken(
    a: str = typer.Argument(..., help="第一个Token地址"),
    b: str = typer.Argument(..., help="第二个Token地址"),
):
    """
    返回按照 Uniswap 规则排序后的 token0 和 token1
    """
    # 移除可能存在的 "0x" 前缀
    addr_a = a.lower().replace("0x", "")
    addr_b = b.lower().replace("0x", "")

    # 验证地址格式是否正确
    if len(addr_a) != 40 or len(addr_b) != 40:
        print("错误: 地址必须是40位十六进制字符串")
        return

    # 按照Uniswap的方式进行比较（基于数值大小而不是字符串排序）
    if int(addr_a, 16) < int(addr_b, 16):
        token0, token1 = a, b
    else:
        token0, token1 = b, a

    print(token0, token1)
    return token0, token1


def say():
    cli()


if __name__ == "__main__":
    usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    usdt = "0xdac17f958d2ee523a2206206994597c13d831ec7"
    xaut = "0x68749665ff8d2d112fa859aa293f07a622782f38"
    uni = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"
    aave = "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9"
    stoken(usdt, xaut)
