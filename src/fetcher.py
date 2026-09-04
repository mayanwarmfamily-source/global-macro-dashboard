# -*- coding: utf-8 -*-
"""
数据抓取引擎：统一调度 FRED、AkShare 和 yfinance API，
包含指数退避重试与异常降级防护机制，确保 CI/CD 环境下流水线不崩溃。
"""

import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred
import yfinance as yf

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DataFetcher:
    def __init__(self, fred_api_key: str):
        self.fred = Fred(api_key=fred_api_key) if fred_api_key else None
        if not self.fred:
            logging.warning("⚠️ 未提供 FRED_API_KEY，FRED 数据拉取将被跳过！")

    def _fetch_fred_series(self, series_id: str, retries: int = 3) -> pd.Series:
        """从 FRED 抓取数据，带指数退避重试机制"""
        if not self.fred:
            return pd.Series(dtype=float)
            
        for attempt in range(retries):
            try:
                # 动态计算开始时间（拉取过去 3 年数据，确保 YoY 计算有足够的历史缓存）
                start_date = (datetime.now() - timedelta(days=365 * 3)).strftime('%Y-%m-%d')
                data = self.fred.get_series(series_id, observation_start=start_date)
                if not data.empty:
                    data.index = pd.to_datetime(data.index)
                    return data
            except Exception as e:
                logging.warning(f"⚠️ FRED [{series_id}] 拉取失败 (尝试 {attempt + 1}/{retries}): {e}")
                time.sleep(2 ** attempt)
        logging.error(f"❌ FRED [{series_id}] 最终拉取失败！")
        return pd.Series(dtype=float)

    def _fetch_akshare_series(self, code: str, retries: int = 3) -> pd.Series:
        """从 AkShare 抓取中国官方宏观数据，带容错机制"""
        import akshare as ak
        for attempt in range(retries):
            try:
                if code == "macro_china_gdp_monthly":
                    df = ak.macro_china_gdp_monthly()
                    # 数据清洗：选择季度和同比增速
                    df['date'] = pd.to_datetime(df['季度'], errors='coerce')
                    df = df.dropna(subset=['date']).set_index('date')
                    return df['国内生产总值-绝对值'].astype(float) # 可根据需要选增速
                
                elif code == "macro_china_cpi_monthly":
                    df = ak.macro_china_cpi_monthly()
                    df['date'] = pd.to_datetime(df['月份'], format='%Y.%m', errors='coerce')
                    df = df.dropna(subset=['date']).set_index('date')
                    return df['全国-同比'].astype(float)

                elif code == "macro_china_shrf":
                    df = ak.macro_china_shrf()
                    df['date'] = pd.to_datetime(df['月份'], format='%Y.%m', errors='coerce')
                    df = df.dropna(subset=['date']).set_index('date')
                    return df['社会融资规模增量'].astype(float)
            except Exception as e:
                logging.warning(f"⚠️ AkShare [{code}] 拉取失败 (尝试 {attempt + 1}/{retries}): {e}")
                time.sleep(2 ** attempt)
        logging.error(f"❌ AkShare [{code}] 最终拉取失败，将降级处理。")
        return pd.Series(dtype=float)

    def _fetch_yfinance_series(self, ticker: str) -> pd.Series:
        """从 yfinance 抓取行情数据（如 BDI 指数）"""
        try:
            df = yf.Ticker(ticker).history(period="2y")
            if not df.empty:
                return df['Close']
        except Exception as e:
            logging.error(f"❌ yfinance [{ticker}] 拉取失败: {e}")
        return pd.Series(dtype=float)

    def fetch_all(self, charts_config: list) -> dict:
        """根据 config.yaml 中的图表配置，拉取所有需要的原始数据"""
        raw_data = {}
        logging.info("🚀 开始并行/依次拉取全球宏观指标数据...")

        for chart in charts_config:
            for s in chart.get("series", []):
                source = s.get("source")
                code = s.get("code")
                key = f"{source}:{code}"

                if key in raw_data:
                    continue  # 避免重复拉取相同序列

                logging.info(f"📥 正在拉取: [{source.upper()}] {code} ...")
                if source == "fred":
                    raw_data[key] = self._fetch_fred_series(code)
                elif source == "akshare":
                    raw_data[key] = self._fetch_akshare_series(code)
                elif source == "yfinance":
                    raw_data[key] = self._fetch_yfinance_series(code)

        logging.info("✅ 所有原始数据拉取完毕！")
        return raw_data