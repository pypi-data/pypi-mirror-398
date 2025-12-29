from thsdk import THS
import pandas as pd
import time

with THS() as ths:
    start_time = time.perf_counter()
    response = ths.corporate_action("USZA300033")
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print("权息资料:")

    if not response:
        print(response.error)
    else:
        print(response.df)
    print(f"运行时间: {execution_time:.5f} 秒\n")

    time.sleep(1)
