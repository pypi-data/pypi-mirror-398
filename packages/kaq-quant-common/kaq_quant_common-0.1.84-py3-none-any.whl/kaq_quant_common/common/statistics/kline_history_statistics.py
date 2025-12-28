import datetime
import json
from typing import Optional

import pandas as pd
from pydantic import BaseModel

from kaq_quant_common.utils import logger_utils

platforms = ["binance", "bitget", "bybit", "gate", "htx", "okx"]


# 对比结果结构体
class StatisticsInfo(BaseModel):
    # 对比平台
    platform: str
    # 标准差
    std: float
    # 平均值
    mean: float
    # 最大值
    max: float
    # 皮尔逊系数(斜率)
    corr: float
    # 最小值
    min: float
    # 4分位数
    quantile: dict[str, float]
    # 相隔时间(hour)
    period: Optional[int] = 0


# 这个类是统计合约K线历史数据的，在确保已经抓取完数据后使用
class FuturesKlineHistoryStatistics:
    def __init__(
        self,
        begin_timestamp: int,
        end_timestamp: int,
        symbols: list[str],
        master: str,
        redis: None,
        mysql: None,
    ):
        self.redis_key = "kaq_futures_kline_history_statistics"
        self.begin_timestamp = begin_timestamp
        self.end_timestamp = end_timestamp
        self.symbols = symbols
        # 计算天数，每天都会有1440条数据
        self.day_num = (end_timestamp - begin_timestamp) // (24 * 3600 * 1000)
        self._redis = redis
        self._mysql = mysql
        self.master = master
        self._logger = logger_utils.get_logger()

    # 针对本平台的所有交易对每个进行对应统计
    def symbols_statistics(self):
        for symbol in self.symbols:
            try:
                self.get_symbol_kline_all_platform(symbol)
            except Exception as e:
                self._logger.error(f"拉取{symbol}的K线数据出现异常: {e}")
                continue

    # 对指定交易对进行全平台的K线拉取
    def get_symbol_kline_all_platform(self, symbol: str):
        df_dict = {}
        # 先拉自己的吧
        master_df = self.query_symbol_line_data(symbol, self.master)

        # 不够数据也跳过
        if len(master_df) < 1440 * self.day_num:
            raise Exception(
                f"{self.master}平台拉取到的{symbol}的K线数据量不足{1440 * self.day_num}条，跳过后续处理"
            )

        # 对其它交易所进行拉取
        for platform in platforms:
            if platform == self.master:
                continue
            platform_df = self.query_symbol_line_data(symbol, platform)

            if len(platform_df) < 1440 * self.day_num:
                self._logger.error(
                    f"{platform}平台拉取到的{symbol}的K线数据量不足{1440 * self.day_num}条，跳过该交易所数据"
                )
                continue

            df_dict[platform] = platform_df

        #  开始计算差异
        symbol_diffrenence_dict = self.calculate_kline_difference(
            symbol, master_df, df_dict
        )

        self._redis.hset(
            self.redis_key + ":" + self.master.upper(),
            symbol,
            json.dumps({k: v.model_dump() for k, v in symbol_diffrenence_dict.items()}),
        )

    # 计算各个平台的K线差异
    def calculate_kline_difference(
        self, symbol: str, master_df: pd.DataFrame, df_dict: dict
    ):
        res = {}
        # 自己也要计算差异
        master_std = master_df[f"{self.master}_close"].std()
        master_mean = master_df[f"{self.master}_close"].mean()
        master_max = master_df[f"{self.master}_close"].max()
        master_rate_corr = master_df[f"{self.master}_close"].corr(
            master_df["event_time"]
        )
        master_min = master_df[f"{self.master}_close"].min()
        master_quantile = master_df[f"{self.master}_close"].quantile([0.25, 0.5, 0.75])

        res[self.master] = StatisticsInfo(
            platform=self.master,
            std=master_std,
            mean=master_mean,
            max=master_max,
            corr=master_rate_corr,
            min=master_min,
            quantile={str(k): float(v) for k, v in master_quantile.to_dict().items()},
        )
        for platform, platform_df in df_dict.items():
            # 合并数据，找出差异
            merged_df = pd.merge(
                master_df, platform_df, on=["symbol", "event_time"], how="inner"
            )
            # 计算差值
            merged_df["close_diff"] = (
                merged_df[f"{self.master}_close"] - merged_df[f"{platform}_close"]
            )
            # 标准差
            close_std = merged_df["close_diff"].std()
            # 平均值
            close_mean = merged_df["close_diff"].mean()
            # 最大值
            close_max = merged_df["close_diff"].max()
            # 皮尔逊系数(斜率)
            close_corr = merged_df["close_diff"].corr(merged_df["event_time"])
            # 最小值
            close_min = merged_df["close_diff"].min()
            # 4分位数
            close_quantile = merged_df["close_diff"].quantile([0.25, 0.5, 0.75])
            # self._logger.info(
            #     f"{self.master}与{platform}平台的{symbol}的K线差异统计: 标准差={close_std}, 平均值={close_mean}, 最大值={close_max}, 最小值={close_min}, 皮尔逊系数={close_corr}, 四分位数={close_quantile.to_dict()}"
            # )
            res[platform] = StatisticsInfo(
                platform=platform,
                std=close_std,
                mean=close_mean,
                max=close_max,
                corr=close_corr,
                min=close_min,
                quantile={str(k): float(v) for k, v in close_quantile.to_dict().items()},
            )

        return res

    # 拉指定时间指定symbol的k线数据
    def query_symbol_line_data(self, symbol: str, platform: str):
        sql_result_df = pd.DataFrame()
        zero_timestamp_list = self.get_zero_timestamp_list()
        # 表前缀
        table_name_prefix = f"kaq_{platform}_futures_kline_history"
        for ts in zero_timestamp_list:
            # 先转成周一日期来定表名，因为数据表是按周来分表的
            date_str = self.get_monday_time(ts)
            table_name = f"{table_name_prefix}_{date_str}"
            sql = f"select exchange, symbol, close as {platform}_close, event_time from {table_name} where symbol = '{symbol}' and event_time >= {ts} and event_time < {ts + 86400000} order by event_time desc ;"
            result = self._mysql.fetch_data(sql)
            sql_result_df = pd.concat([sql_result_df, result], ignore_index=True)

        return sql_result_df

    # 计算某个时间戳对应的周一日期字符串
    def get_monday_time(self, timestamp):
        dt = datetime.datetime.fromtimestamp(timestamp / 1000)
        monday = dt - datetime.timedelta(days=dt.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        return monday.strftime("%Y%m%d")

    # 计算开始到结束时间所有的0时时间戳
    def get_zero_timestamp_list(self):
        # 毫秒转日期
        timestamp_list = []
        begin_date = datetime.datetime.fromtimestamp(
            self.begin_timestamp // 1000, datetime.UTC
        ).date()
        end_date = datetime.datetime.fromtimestamp(
            self.end_timestamp // 1000, datetime.UTC
        ).date()
        cur = begin_date
        while cur <= end_date:
            # 0点时间戳（毫秒）
            dt = datetime.datetime.combine(
                cur, datetime.time(0, 0), tzinfo=datetime.UTC
            )
            ts = int(dt.timestamp() * 1000)
            timestamp_list.append(ts)
            cur += datetime.timedelta(days=1)

        return timestamp_list


if __name__ == "__main__":
    klineStatistics = FuturesKlineHistoryStatistics(
        1765296000000, 1765382400000, ["BTCUSDT", "ETHUSDT"]
    )
    klineStatistics.symbols_statistics()
