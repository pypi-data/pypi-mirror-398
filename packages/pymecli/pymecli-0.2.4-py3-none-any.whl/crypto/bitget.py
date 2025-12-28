from decimal import Decimal

import requests
from sqlalchemy import Engine

from utils.mysql import mysql_to_csv


def tickers(url: str, symbols: list, proxy: str | None = None):
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy,
        }
    response = requests.get(url, proxies=proxies)

    resp_json = response.json()
    symbols_list = [
        s.lower() + "usdt" if not s.lower().endswith("usdt") else s.lower()
        for s in symbols
    ]
    if response.status_code == 200 and resp_json.get("code") == "00000":
        data = resp_json.get("data", [])
        results = []
        for item in data:
            if item["symbol"].lower() in symbols_list:
                price = Decimal(item["lastPr"])
                results.append(
                    f"{item['symbol'].upper().rstrip('USDT')}:{format(price, 'f')}"
                )
        print(f"[{','.join(results)}]")
    else:
        print(
            f"📌 请求失败,状态码:{response.status_code},错误信息:{resp_json.get('msg')}"
        )


def mix_tickers(symbols: list, proxy: str | None = None):
    url = "https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES"
    tickers(url, symbols, proxy)


def spot_tickers(symbols: list, proxy: str | None = None):
    url = "https://api.bitget.com/api/v2/spot/market/tickers"
    tickers(url, symbols, proxy)


def bitget_sf_open(engine: Engine, csv_path: str):
    query = "select * from bitget_sf where spot_open_usdt is not null and futures_open_usdt is not null and pnl is null and up_status = 0 and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget_sf",
        query,
        update_status=1,
        d_column_names=["spot_client_order_id", "futures_client_order_id"],
        pd_dtype={
            "spot_order_id": str,
            "futures_order_id": str,
            "spot_tracking_no": str,
            "futures_tracking_no": str,
        },
    )

    print(f"🚀 bitget sf open count:({row_count})")


def bitget_sf_close(engine: Engine, csv_path: str):
    query = "select * from bitget_sf where pnl is not null and up_status in (0,1);"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget_sf",
        query,
        update_status=2,
        d_column_names=["spot_client_order_id", "futures_client_order_id"],
        pd_dtype={
            "spot_order_id": str,
            "futures_order_id": str,
            "spot_tracking_no": str,
            "futures_tracking_no": str,
        },
    )

    print(f"🚀 bitget sf close count:({row_count})")


def grid_open(engine: Engine, csv_path: str):
    query = "select id,created_at,name,act_name,symbol,qty,cex,status,up_status,path,level,earn,cost,buy_px,benefit,sell_px,profit,order_id,client_order_id,fx_order_id,fx_client_order_id,signature,chain,open_at,close_at,mint,dex_act,dex_status,dex_fail_count from bitget where ((cost is not null or benefit is not null) and profit is null) and up_status = 0 and order_id is not null and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget",
        query,
        update_status=1,
        d_column_names=["client_order_id"],
        pd_dtype={
            "order_id": str,
            "fx_order_id": str,
        },
    )
    print(f"🧮 bitget open count:({row_count})")


def grid_close(engine: Engine, csv_path: str):
    query = "select id,created_at,name,act_name,symbol,qty,cex,status,up_status,path,level,earn,cost,buy_px,benefit,sell_px,profit,order_id,client_order_id,fx_order_id,fx_client_order_id,signature,chain,open_at,close_at,mint,dex_act,dex_status,dex_fail_count from bitget where profit is not null and up_status in (0,1) and deleted_at is null;"
    row_count = mysql_to_csv(
        engine,
        csv_path,
        "bitget",
        query,
        update_status=2,
        d_column_names=["client_order_id"],
        pd_dtype={
            "order_id": str,
            "fx_order_id": str,
        },
    )
    print(f"🧮 bitget close count:({row_count})")


if __name__ == "__main__":
    pass
