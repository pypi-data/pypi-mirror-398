# encoding: utf-8
"""
THS SDK 测试模块
用于测试和统计API调用情况
"""
import time
from typing import Dict, List, Tuple, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from thsdk import THS, Response


class APITestResult:
    """API测试结果统计类"""

    def __init__(self):
        self.total_tests = 0
        self.success_tests = 0
        self.failed_tests = 0
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    def add_test(self, api_name: str, success: bool, error: str = "",
                 execution_time: float = 0, data_count: int = 0):
        """添加测试结果"""
        self.total_tests += 1
        if success:
            self.success_tests += 1
        else:
            self.failed_tests += 1

        self.test_results.append({
            "api_name": api_name,
            "success": success,
            "error": error,
            "execution_time": execution_time,
            "data_count": data_count,
            "timestamp": datetime.now().isoformat()
        })

    def print_summary(self):
        """打印测试统计摘要"""
        if self.end_time and self.start_time:
            total_time = (self.end_time - self.start_time).total_seconds()
        else:
            total_time = 0

        print("\n" + "=" * 70)
        print("API 测试统计报告")
        print("=" * 70)
        print(f"总测试数: {self.total_tests}")
        print(
            f"成功: {self.success_tests} ({self.success_tests / self.total_tests * 100:.1f}%)" if self.total_tests > 0 else "成功: 0")
        print(
            f"失败: {self.failed_tests} ({self.failed_tests / self.total_tests * 100:.1f}%)" if self.total_tests > 0 else "失败: 0")
        print(f"总耗时: {total_time:.2f} 秒")
        if self.total_tests > 0:
            print(f"平均耗时: {total_time / self.total_tests:.3f} 秒/次")
        print("=" * 70)

        # 打印失败的测试
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print("\n失败的API调用:")
            for result in failed_tests:
                print(f"  - {result['api_name']}: {result['error']}")

        # 打印成功的测试详情
        print("\n成功的API调用详情:")
        for result in self.test_results:
            if result["success"]:
                status = "✓"
                data_info = f", 数据量: {result['data_count']}" if result['data_count'] > 0 else ""
                print(f"  {status} {result['api_name']}: "
                      f"耗时 {result['execution_time']:.3f}秒{data_info}")
            else:
                status = "✗"
                print(f"  {status} {result['api_name']}: {result['error']}")
        print("=" * 70 + "\n")


def test_api_call(test_result: APITestResult, api_name: str,
                  func, *args, **kwargs) -> Tuple[bool, Response, float]:
    """
    测试API调用

    Args:
        test_result: 测试结果统计对象
        api_name: API名称
        func: 要测试的函数
        *args, **kwargs: 函数参数

    Returns:
        (success, response, execution_time) 元组
    """
    start_time = time.perf_counter()
    try:
        response = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        success = bool(response) and response.success
        error = response.error if not success else ""

        # 统计数据量
        data_count = 0
        if response and response.data:
            if isinstance(response.data, list):
                data_count = len(response.data)
            elif isinstance(response.data, dict):
                data_count = 1
            elif isinstance(response.data, str):
                data_count = len(response.data) if response.data else 0

        test_result.add_test(api_name, success, error, execution_time, data_count)
        return success, response, execution_time
    except Exception as e:
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        error_msg = str(e)
        test_result.add_test(api_name, False, error_msg, execution_time, 0)
        return False, None, execution_time


def run_basic_tests(ths: THS) -> APITestResult:
    """运行基础API测试"""
    test_result = APITestResult()
    test_result.start_time = datetime.now()

    print("开始运行基础API测试...")

    # 测试连接
    success, response, _ = test_api_call(test_result, "connect", ths.connect)
    if not success:
        print("连接失败，无法继续测试")
        test_result.end_time = datetime.now()
        return test_result

    time.sleep(0.5)

    # 测试获取板块数据
    test_api_call(test_result, "block(沪深A股)", ths.block, 0xE)
    time.sleep(0.1)

    # 测试获取行业板块
    test_api_call(test_result, "ths_industry", ths.ths_industry)
    time.sleep(0.1)

    # 测试获取概念板块
    test_api_call(test_result, "ths_concept", ths.ths_concept)
    time.sleep(0.1)

    # 测试获取指数列表
    test_api_call(test_result, "index_list", ths.index_list)
    time.sleep(0.1)

    # 测试获取A股列表
    test_api_call(test_result, "stock_cn_lists", ths.stock_cn_lists)
    time.sleep(0.1)

    # 测试深度数据
    test_api_call(test_result, "depth(单只)", ths.depth, "USZA300033")
    time.sleep(0.1)

    # 测试K线数据
    test_api_call(test_result, "klines(日线)", ths.klines, "USZA300033", count=10)
    time.sleep(0.1)

    # 测试市场数据
    test_api_call(test_result, "market_data_cn", ths.market_data_cn, "USZA300033")
    time.sleep(0.1)

    # 测试集合竞价
    test_api_call(test_result, "call_auction", ths.call_auction, "USZA300033")
    time.sleep(0.1)

    # 测试日内分时数据
    test_api_call(test_result, "intraday_data", ths.intraday_data, "USZA300033")
    time.sleep(0.1)

    # 测试tick数据
    test_api_call(test_result, "tick_level1", ths.tick_level1, "USZA300033")
    time.sleep(0.1)

    # 测试问财查询
    test_api_call(test_result, "wencai_nlp", ths.wencai_nlp, "涨停")
    time.sleep(0.1)

    # 测试代码标准化
    test_api_call(test_result, "normalize_symbol", ths.normalize_symbol, "300033")
    time.sleep(0.1)

    test_result.end_time = datetime.now()
    return test_result


def run_advanced_tests(ths: THS) -> APITestResult:
    """运行高级API测试"""
    test_result = APITestResult()
    test_result.start_time = datetime.now()

    print("开始运行高级API测试...")

    # 确保已连接
    if not ths._initialized:
        success, response, _ = test_api_call(test_result, "connect", ths.connect)
        if not success:
            print("连接失败，无法继续测试")
            test_result.end_time = datetime.now()
            return test_result
        time.sleep(0.5)

    # 测试不同市场的股票列表
    test_api_call(test_result, "stock_us_lists", ths.stock_us_lists)
    time.sleep(0.1)

    test_api_call(test_result, "stock_hk_lists", ths.stock_hk_lists)
    time.sleep(0.1)

    test_api_call(test_result, "stock_uk_lists", ths.stock_uk_lists)
    time.sleep(0.1)

    # 测试不同市场的数据
    test_api_call(test_result, "market_data_us", ths.market_data_us, "UNQQTSLA")
    time.sleep(0.1)

    test_api_call(test_result, "market_data_hk", ths.market_data_hk, "UEUACPIC")
    time.sleep(0.1)

    # 测试基金ETF
    test_api_call(test_result, "fund_etf_lists", ths.fund_etf_lists)
    time.sleep(0.1)

    test_api_call(test_result, "market_data_fund", ths.market_data_fund, "USZJ159629")
    time.sleep(0.1)

    # 测试债券
    test_api_call(test_result, "bond_lists", ths.bond_lists)
    time.sleep(0.1)

    test_api_call(test_result, "market_data_bond", ths.market_data_bond, "USHD113037")
    time.sleep(0.1)

    # 测试期货
    test_api_call(test_result, "futures_lists", ths.futures_lists)
    time.sleep(0.1)

    # 测试外汇
    test_api_call(test_result, "forex_list", ths.forex_list)
    time.sleep(0.1)

    test_api_call(test_result, "market_data_forex", ths.market_data_forex, "UFXBUSDCNY")
    time.sleep(0.1)

    # 测试指数数据
    test_api_call(test_result, "market_data_index", ths.market_data_index, "USHI1B0935")
    time.sleep(0.1)

    # 测试不同周期的K线
    bj_tz = ZoneInfo('Asia/Shanghai')
    test_api_call(test_result, "klines(1分钟)", ths.klines, "USZA300033", count=10, interval="1m")
    time.sleep(0.1)

    test_api_call(test_result, "klines(5分钟)", ths.klines, "USZA300033", count=10, interval="5m")
    time.sleep(0.1)

    test_api_call(test_result, "klines(前复权)", ths.klines, "USZA300033", count=10, adjust="forward")
    time.sleep(0.1)

    test_result.end_time = datetime.now()
    return test_result


def main():
    """主测试函数"""
    print("=" * 70)
    print("THS SDK API 测试工具")
    print("=" * 70)

    ths = THS()

    try:
        # 运行基础测试
        basic_result = run_basic_tests(ths)
        basic_result.print_summary()

        time.sleep(1)

        # 运行高级测试
        advanced_result = run_advanced_tests(ths)
        advanced_result.print_summary()

        # 合并统计
        print("\n" + "=" * 70)
        print("总体测试统计")
        print("=" * 70)
        total_tests = basic_result.total_tests + advanced_result.total_tests
        total_success = basic_result.success_tests + advanced_result.success_tests
        total_failed = basic_result.failed_tests + advanced_result.failed_tests

        if basic_result.start_time and advanced_result.end_time:
            total_time = (advanced_result.end_time - basic_result.start_time).total_seconds()
        else:
            total_time = 0

        print(f"总测试数: {total_tests}")
        print(f"成功: {total_success} ({total_success / total_tests * 100:.1f}%)" if total_tests > 0 else "成功: 0")
        print(f"失败: {total_failed} ({total_failed / total_tests * 100:.1f}%)" if total_tests > 0 else "失败: 0")
        print(f"总耗时: {total_time:.2f} 秒")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ths.disconnect()
        print("已断开连接")


if __name__ == "__main__":
    main()

