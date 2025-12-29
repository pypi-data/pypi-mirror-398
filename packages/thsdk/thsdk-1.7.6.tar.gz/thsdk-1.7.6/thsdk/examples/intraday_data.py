from thsdk import THS
import pandas as pd
import time

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
with THS() as ths:
    response = ths.intraday_data("USZA300033")
    print("股票日内分时数据:")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        print(response.df)
    time.sleep(1)

    response = ths.intraday_data("USHI1A0001")
    print("指数日内分时数据:")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        print(response.df)
    time.sleep(1)
