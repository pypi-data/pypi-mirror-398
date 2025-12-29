from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    response = ths.ths_concept()
    print("概念:")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        print(response.df)
    time.sleep(1)
