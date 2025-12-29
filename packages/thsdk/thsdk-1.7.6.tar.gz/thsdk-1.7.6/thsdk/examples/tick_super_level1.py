from thsdk import THS
import pandas as pd
import time

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
with THS() as ths:
    print("当日 超级盘口带买卖5档位盘口:")
    response = ths.tick_super_level1("USZA002632")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        df = response.df
        df["时间"] = pd.to_datetime(df["时间"], unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Shanghai")
        print(df)
    time.sleep(1)

    print("历史 超级盘口带买卖5档位盘口:")
    response = ths.tick_super_level1("USZA300033", "20250701")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        df = response.df
        df["时间"] = pd.to_datetime(df["时间"], unit="s").dt.tz_localize("UTC").dt.tz_convert("Asia/Shanghai")
        print(df)
    time.sleep(1)
