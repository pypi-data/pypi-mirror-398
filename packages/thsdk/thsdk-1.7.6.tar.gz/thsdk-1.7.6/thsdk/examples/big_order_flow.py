import time

from thsdk import THS
import pandas as pd

# 股票代码（可自行修改）
stock_code = "USZA300033"  # 示例：创业板ETF 或其他代码

with THS() as ths:
    print(f"正在查询 {stock_code} 的大单棱镜数据...\n")

    response = ths.big_order_flow(stock_code)

    if not response or response.df is None or response.df.empty:
        print("获取数据失败或数据为空")
        if hasattr(response, 'error') and response.error:
            print(f"错误信息: {response.error}")
        exit()

    df = response.df.copy()  # 复制一份避免修改原始数据

    # 时间处理
    df['时间'] = pd.to_datetime(df['时间'], unit='s', utc=True, errors='coerce')
    df = df.dropna(subset=['时间'])  # 丢弃无效时间行
    df['时间'] = df['时间'].dt.tz_convert('Asia/Shanghai')

    # 创建分钟级时间戳（floor到分钟）
    df['分钟'] = df['时间'].dt.floor('min')

    # 清理不必要的列（如果存在）
    drop_cols = ['委托买入价', '委托卖出价']
    df = df.drop(columns=[col for col in drop_cols if col in df.columns], errors='ignore')

    # 打印原始数据概览（可选，调试用）
    print("前5行原始数据：")
    print(df.head())
    print("-" * 60)

    # 计算每笔的资金流向符号（主被动统一处理）
    direction_map = {1: 1, 2: 1, -1: -1, -2: -1}  # 买入正，卖出负
    df['净额符号'] = df['成交方向'].map(direction_map).fillna(0)
    df['净额_元'] = df['总金额'] * df['净额符号']

    # ────────────── 整体统计 ──────────────
    print("\n【整体大单统计】")
    total_buy_active = df[df['成交方向'] == 1]['总金额'].sum() / 10000
    total_sell_active = df[df['成交方向'] == -1]['总金额'].sum() / 10000
    total_buy_passive = df[df['成交方向'] == 2]['总金额'].sum() / 10000
    total_sell_passive = df[df['成交方向'] == -2]['总金额'].sum() / 10000

    print(f"主动买入 : {total_buy_active:12,.2f} 万")
    print(f"主动卖出 : {total_sell_active:12,.2f} 万")
    print(f"被动买入 : {total_buy_passive:12,.2f} 万")
    print(f"被动卖出 : {total_sell_passive:12,.2f} 万")
    print("-" * 40)

    net_main_passive = (total_buy_active + total_buy_passive - total_sell_active - total_sell_passive)
    net_main_only = (total_buy_active - total_sell_active)

    print(f"净额(主被动) : {net_main_passive:12,.2f} 万")
    print(f"净额(仅主动): {net_main_only:12,.2f} 万")
    print("=" * 60)

    # ────────────── 按分钟统计 ──────────────
    print("\n【按分钟统计 - 主被动净额】（正数=资金净流入）")

    minute_stats = df.groupby('分钟').agg(
        主被动流入_万元=('净额_元', lambda x: x[x > 0].sum() / 10000),
        主被动流出_万元=('净额_元', lambda x: x[x < 0].sum() / 10000),
        净额_万元=('净额_元', lambda x: x.sum() / 10000),
        总笔数=('总金额', 'count'),
        总金额_万元=('总金额', lambda x: x.sum() / 10000)
    ).reset_index()

    # 格式化显示
    minute_stats = minute_stats.round(2)
    minute_stats['累计净额_万元'] = minute_stats['净额_万元'].cumsum().round(2)

    # 调整列顺序，更直观
    cols_order = ['分钟', '净额_万元', '累计净额_万元', '主被动流入_万元', '主被动流出_万元', '总笔数', '总金额_万元']
    minute_stats = minute_stats[cols_order]

    # 排序（时间顺序）
    minute_stats = minute_stats.sort_values('分钟')

    print(minute_stats.to_string(index=False))
    print("=" * 60)

    # 可选：保存到csv方便后续分析
    # minute_stats.to_csv(f"minute_netflow_{stock_code}.csv", index=False, encoding='utf-8-sig')
    # print(f"\n已保存分钟级净额数据至: minute_netflow_{stock_code}.csv")

    time.sleep(1)