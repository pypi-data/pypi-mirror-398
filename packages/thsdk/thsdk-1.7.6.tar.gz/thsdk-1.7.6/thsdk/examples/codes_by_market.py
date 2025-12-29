from thsdk import THS
import pandas as pd
import time
from zoneinfo import ZoneInfo

bj_tz = ZoneInfo('Asia/Shanghai')

with THS() as ths:
    markets = [
        ("USHA", "沪市场"),
        ("USZA", "深市场"),
        ("USTM", "京市场"),
        ("UNQS", "美股纳斯达克"),
        ("UFXB", "汇率市场"),
        ("USHI", "沪指数"),
        ("UIFB", "期权"),
        ("UEUA", "英国"),
    ]

    for code, name in markets:
        response = ths.market_block(code)
        print(f"\n{name}({code}):")
        if not response:
            print(f"❌ 错误信息: {response.error}")
        else:
            df = response.df
            if df.empty:
                print("⚠️ 无数据返回")
            else:
                print(df)
        time.sleep(0.1)




