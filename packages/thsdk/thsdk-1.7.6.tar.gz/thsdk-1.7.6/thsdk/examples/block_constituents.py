from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    response = ths.block_constituents("URFI886037")
    print("板块成份股数据:")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        print(response.df)

    time.sleep(1)
