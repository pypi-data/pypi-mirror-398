from thsdk import THS
import pandas as pd
import time

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
with THS() as ths:
    response = ths.depth("USZA300033")
    print("单只五档:")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        print(response.df)
    time.sleep(1)

    response = ths.depth(["USZA300033", "USZA300750"])
    print("多支五档:")
    if not response:
        print(f"错误信息: {response.error}")
    else:
        print(response.df)
    time.sleep(1)
