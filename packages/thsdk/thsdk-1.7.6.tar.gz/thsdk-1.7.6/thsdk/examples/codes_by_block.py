from thsdk import THS
import pandas as pd
import time
from zoneinfo import ZoneInfo

bj_tz = ZoneInfo('Asia/Shanghai')

with THS() as ths:
    block_funcs = [
        (ths.stock_cn_lists, "A股"),
        (ths.stock_us_lists, "美股"),
        (ths.nasdaq_lists, "纳斯达克"),
        (ths.stock_hk_lists, "港股"),
        (ths.stock_b_lists, "B股"),
        (ths.stock_bj_lists, "北交所"),
    ]

    for func, label in block_funcs:
        print(f"\n==== {label} ====")
        response = func()
        if not response:
            print(f"❌ 错误信息: {response.error}")
        else:
            df = response.df
            if df.empty:
                print(f"⚠️ 无数据返回")
            else:
                print(df)
        time.sleep(1)
