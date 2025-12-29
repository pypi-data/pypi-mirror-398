from thsdk import THS
import pandas as pd
import time

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 180)

def show_tick_level1(symbol: str):
    with THS() as ths:
        print(f"{symbol} 的tick历史数据:")
        response = ths.tick_level1(symbol)
        if not response:
            print(f"❌ 错误信息: {response.error}")
            return
        df = response.df
        if "时间" in df.columns:
            df["时间"] = pd.to_datetime(df["时间"], unit="s", utc=True).dt.tz_convert("Asia/Shanghai")
        print(df)
        time.sleep(1)

if __name__ == "__main__":
    show_tick_level1("USZA300033")
