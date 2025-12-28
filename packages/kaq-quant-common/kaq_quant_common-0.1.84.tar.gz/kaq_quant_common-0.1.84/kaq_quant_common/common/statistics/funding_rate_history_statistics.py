import datetime
import json
from typing import Optional

import pandas as pd
from pydantic import BaseModel

from kaq_quant_common.common.statistics.kline_history_statistics import \
    StatisticsInfo
from kaq_quant_common.utils import logger_utils

platforms = ["binance", "bitget", "bybit", "gate", "htx", "okx"]


# 这个类是统计合约历史资金数据的，在确保已经抓取完数据后使用
class FuturesFundingRateHistoryStatistics:
    def __init__(
        self,
        begin_timestamp: int,
        end_timestamp: int,
        symbols: list[str],
        master: str,
        redis: None,
        mysql: None,
    ):
        self.redis_key = "kaq_futures_funding_rate_history_statistics"
        self.begin_timestamp = begin_timestamp
        self.end_timestamp = end_timestamp
        self.symbols = symbols
        # 计算天数
        self.day_num = (end_timestamp - begin_timestamp) // (24 * 3600 * 1000)
        self._redis = redis
        self._mysql = mysql
        self.master = master
        self._logger = logger_utils.get_logger()
        self.table_name = "kaq_futures_funding_rate_history"

    # 针对本平台的所有交易对每个进行对应统计
    def symbols_statistics(self):
        for symbol in self.symbols:
            try:
                self.get_symbol_funding_rate_all_platform(symbol)
            except Exception as e:
                self._logger.error(f"拉取{symbol}的资金数据出现异常: {e}")
                ddd = 1
                continue

    # 对指定交易对进行全平台的资金数据拉取
    def get_symbol_funding_rate_all_platform(self, symbol: str):
        df_dict = {}
        # 先拉自己的吧
        master_df = self.query_symbol_funding_rate_data(symbol, self.master)

        # 先记录下主平台拉到的数据量，用来对比其它平台，其它平台不是这么多就证明有问题，需要记录下日志
        master_df_len = len(master_df)

        # 没有数据就跳过
        if master_df_len == 0:
            raise Exception(
                f"{self.master}平台拉取到的{symbol}的资金数据量为：{master_df_len}条，跳过后续处理"
            )

        # 对其它交易所进行拉取
        for platform in platforms:
            if platform == self.master:
                continue
            platform_df = self.query_symbol_funding_rate_data(symbol, platform)

            if len(platform_df) != master_df_len:
                self._logger.error(
                    f"{platform}平台拉取到的{symbol}的资金数据量与主平台不一致，主平台：{master_df_len},{platform}平台：{len(platform_df)}，跳过该交易所数据"
                )
                continue

            df_dict[platform] = platform_df

        #  开始计算差异
        symbol_diffrenence_dict = self.calculate_funding_rate_difference(
            symbol, master_df, df_dict
        )

        self._redis.hset(
            self.redis_key + ":" + self.master.upper(),
            symbol,
            json.dumps({k: v.model_dump() for k, v in symbol_diffrenence_dict.items()}),
        )

    # 计算各个平台的资金数据差异
    def calculate_funding_rate_difference(
        self, symbol: str, master_df: pd.DataFrame, df_dict: dict
    ):
        res = {}
        master_hour = master_df.iloc[0]["hour"]
        # 自己也要计算差异
        master_std = master_df[f"{self.master}_rate"].std()
        master_mean = master_df[f"{self.master}_rate"].mean()
        master_max = master_df[f"{self.master}_rate"].max()
        master_rate_corr = master_df[f"{self.master}_rate"].corr(
            master_df["event_time_hour"]
        )
        master_min = master_df[f"{self.master}_rate"].min()
        master_quantile = master_df[f"{self.master}_rate"].quantile([0.25, 0.5, 0.75])

        res[self.master] = StatisticsInfo(
            platform=self.master,
            std=master_std,
            mean=master_mean,
            max=master_max,
            corr=master_rate_corr,
            min=master_min,
            quantile={str(k): float(v) for k, v in master_quantile.to_dict().items()},
            period=master_hour,
        )

        # 还要加主平台的差异，主平台不需要减，只需要直接处理
        for platform, platform_df in df_dict.items():
            platform_hour = platform_df.iloc[0]["hour"]
            # 合并数据，找出差异
            merged_df = pd.merge(
                master_df, platform_df, on=["symbol", "event_time_hour"], how="inner"
            )

            # 计算差值
            merged_df["rate_diff"] = (
                merged_df[f"{self.master}_rate"] - merged_df[f"{platform}_rate"]
            )
            # 标准差
            rate_std = merged_df["rate_diff"].std()
            # 平均值
            rate_mean = merged_df["rate_diff"].mean()
            # 最大值
            rate_max = merged_df["rate_diff"].max()
            # 皮尔逊系数(斜率)
            rate_corr = merged_df["rate_diff"].corr(merged_df["event_time_hour"])
            # 最小值
            rate_min = merged_df["rate_diff"].min()
            # 4分位数
            rate_quantile = merged_df["rate_diff"].quantile([0.25, 0.5, 0.75])
            # self._logger.info(
            #     f"{self.master}与{platform}平台的{symbol}的K线差异统计: 标准差={rate_std}, 平均值={rate_mean}, 最大值={rate_max}, 最小值={rate_min}, 皮尔逊系数={rate_corr}, 四分位数={rate_quantile.to_dict()}"
            # )
            res[platform] = StatisticsInfo(
                platform=platform,
                std=rate_std,
                mean=rate_mean,
                max=rate_max,
                corr=rate_corr,
                min=rate_min,
                quantile={str(k): v for k, v in rate_quantile.to_dict().items()},
                period=platform_hour,
            )

        return res

    # 拉指定时间指定symbol的资金数据
    def query_symbol_funding_rate_data(self, symbol: str, platform: str):
        sql_result_df = pd.DataFrame()
        # 先转成周一日期来定表名，因为数据表是按周来分表的
        sql = f"select exchange, symbol, rate as {platform}_rate, event_time from {self.table_name} where symbol = '{symbol}' and event_time >= {self.begin_timestamp} and event_time < {self.end_timestamp} and exchange='{platform}' order by event_time desc ;"
        result = self._mysql.fetch_data(sql)
        sql_result_df = pd.DataFrame(result)
        if sql_result_df.empty:
            return sql_result_df
        # 转换类型
        sql_result_df[f"{platform}_rate"] = sql_result_df[f"{platform}_rate"].astype(
            float
        )
        # 增加个周期字段用来补全24小时数据
        # 我操，接口拿到的event_time毫秒有些不是整点，转成小时处理吧。
        sql_result_df["event_time"] = sql_result_df["event_time"].astype(int)
        sql_result_df["event_time_hour"] = sql_result_df["event_time"] // 1000
        # 计算周期
        sql_result_df["period"] = sql_result_df["event_time_hour"].diff(periods=-1)
        sql_result_df["hour"] = sql_result_df["period"] // 3600

        sql_result_df = sql_result_df[::-1]  # 反向排序

        start_ts = int(sql_result_df["event_time"].iloc[0])
        start_dt = pd.to_datetime(start_ts // 1000, unit="s")
        # 先生成一批完整的时间序列数据
        temp_date_df = pd.date_range(
            start_dt,
            periods=self.day_num * 24,
            freq="h",
        )
        temp_date_df = temp_date_df[::-1]  # 反向排序

        # 生成完整的毫秒级时间戳DataFrame
        temp_time_df = pd.DataFrame(
            {"event_time_hour": temp_date_df.astype(int) // 10**9}  # 转为毫秒
        )
        # 合并，左侧为完整时间
        merged_df = temp_time_df.merge(sql_result_df, on="event_time_hour", how="left")
        # 向上对齐填充
        merged_df = merged_df.sort_values("event_time_hour").ffill()
        # event_time用自身时间，其它字段用ffill
        merged_df["event_time_hour"] = temp_time_df["event_time_hour"]
        merged_df = merged_df.sort_values(
            "event_time_hour", ascending=False
        ).reset_index(drop=True)
        return merged_df


if __name__ == "__main__":
    klineStatistics = FuturesFundingRateHistoryStatistics(
        1765296000000, 1765382400000, ["BTCUSDT", "ETHUSDT"]
    )
    klineStatistics.symbols_statistics()
