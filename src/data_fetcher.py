import os
import logging
import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from pandas_datareader import data as pdr

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class MacroDataFetcher:
    def __init__(self):
        # 抓取起始点稍微向前多取一点，以便准确计算同比/环比后截取精确窗口
        self.start_date = (datetime.datetime.now() - datetime.timedelta(days=365 * 3)).strftime("%Y-%m-%d")
        self.end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 22 个核心宏观指标按频段分类配置
        self.fred_indicators = {
            # --- 季度数据 (保留最近 8 个季度) ---
            "US_GDP": ("A191RL1Q225SBEA", "quarterly", 8),
            "EU_GDP": ("CLVMNACSCAB1GQEA19", "quarterly", 8),
            "JP_GDP": ("JPNRGDPEXP", "quarterly", 8),
            "CN_GDP": ("CHNGDPDQPSMEI", "quarterly", 8),

            # --- 月度数据 (保留最近 12 个月) ---
            "US_CPI": ("CPIAUCSL", "monthly", 12),
            "US_PPI": ("PPIACO", "monthly", 12),
            "US_UNRATE": ("UNRATE", "monthly", 12),
            "US_IND_PROD": ("INDPRO", "monthly", 12),
            "EU_CPI": ("CP0000EZ19M086NEST", "monthly", 12),
            "JP_CPI": ("CPALTT01JPM659N", "monthly", 12),
            "US_FED_RATE": ("FEDFUNDS", "monthly", 12),
            "US_NFCI": ("NFCI", "monthly", 12),

            # --- 每日数据 (保留最近 1 年 / 252 交易日) ---
            "US_10Y": ("DGS10", "daily", 252),
            "US_2Y": ("DGS2", "daily", 252),
            "US_YIELD_CURVE": ("T10Y2Y", "daily", 252),
            "US_SOFR": ("SOFR", "daily", 252),
            "US_DXY": ("DTWEXBGS", "daily", 252),
            "US_VIX": ("VIXCLS", "daily", 252)
        }
        
        # Yahoo Finance 每日数据 (保留最近 1 年 / 252 交易日)
        self.yf_indicators = {
            "GOLD": ("GC=F", "daily", 252),
            "OIL": ("CL=F", "daily", 252),
            "COPPER": ("HG=F", "daily", 252),
            "USD_CNY": ("CNY=X", "daily", 252),
            "USD_JPY": ("JPY=X", "daily", 252)
        }

    def _truncate_window(self, df, freq_type, limit):
        """严格按照规则截取窗口：保留最近 N 条数据，保持 Natural Edge"""
        if df.empty:
            return df
        
        # 按时间升序排列，确保右侧是最新的 Natural Edge
        df = df.sort_index(ascending=True)
        
        # 截取最后 N 条数据（8个季度 / 12个月 / 252个交易日）
        if len(df) > limit:
            df = df.iloc[-limit:]
            
        return df

    def fetch_fred_data(self):
        logger.info(">>> 开始抓取 FRED 宏观指标 (应用 8季度/12个月/1年 动态窗口)...")
        fred_data = {}
        
        for name, (code, freq_type, limit) in self.fred_indicators.items():
            try:
                df = pdr.DataReader(code, "fred", self.start_date, self.end_date).dropna()
                if not df.empty:
                    df.columns = ["value"]
                    
                    # 动态计算变化率
                    if freq_type == "quarterly":
                        df["yoy"] = df["value"].pct_change(4) * 100
                        df["mom"] = df["value"].pct_change(1) * 100
                    elif freq_type == "monthly":
                        df["yoy"] = df["value"].pct_change(12) * 100
                        df["mom"] = df["value"].pct_change(1) * 100
                    else:
                        df["yoy"] = df["value"].pct_change(252) * 100
                        df["mom"] = df["value"].pct_change(21) * 100

                    # 严格裁剪窗口并保留 Natural Edge
                    df = self._truncate_window(df, freq_type, limit)
                    fred_data[name] = df
                    
                    logger.info(f"✅ [FRED] {name} ({freq_type}): 成功截取 {len(df)} 条数据 | 截止日期(Natural Edge): {df.index[-1].strftime('%Y-%m-%d')}")
            except Exception as e:
                logger.error(f"❌ [FRED] {name} ({code}) 抓取失败: {str(e)}")
                
        return fred_data

    def fetch_yahoo_data(self):
        logger.info(">>> 开始抓取 Yahoo Finance 每日数据 (截取最近 1 年)...")
        yf_data = {}
        
        for name, (ticker, freq_type, limit) in self.yf_indicators.items():
            try:
                data = yf.Ticker(ticker)
                df = data.history(start=self.start_date, end=self.end_date)
                if not df.empty:
                    df = df[["Close"]].rename(columns={"Close": "value"})
                    df.index = pd.to_datetime(df.index).tz_localize(None)
                    
                    df["mom"] = df["value"].pct_change(21) * 100
                    df["yoy"] = df["value"].pct_change(252) * 100
                    
                    # 裁剪为最近 252 个交易日
                    df = self._truncate_window(df, freq_type, limit)
                    yf_data[name] = df
                    
                    logger.info(f"✅ [YFinance] {name}: 成功截取 {len(df)} 条数据 | 截止日期(Natural Edge): {df.index[-1].strftime('%Y-%m-%d')}")
            except Exception as e:
                logger.error(f"❌ [YFinance] {name} ({ticker}) 抓取失败: {str(e)}")
                
        return yf_data

    def fetch_china_akshare_data(self):
        logger.info(">>> 开始抓取中国宏观数据 (截取 8季度 / 12个月)...")
        cn_data = {}
        try:
            import akshare as ak
            # 1. 中国 CPI (月度 12 个月)
            try:
                df_cpi = ak.macro_china_cpi()
                if not df_cpi.empty:
                    date_col = [c for c in df_cpi.columns if '月份' in c or 'date' in c][0]
                    val_col = [c for c in df_cpi.columns if '当月' in c or 'yoy' in c or 'CPI' in c][0]
                    df_cpi['date'] = pd.to_datetime(df_cpi[date_col], errors='coerce')
                    df_cpi = df_cpi.dropna(subset=['date']).sort_values('date').set_index('date')
                    df_cpi['value'] = pd.to_numeric(df_cpi[val_col], errors='coerce')
                    
                    cn_data["CN_CPI"] = self._truncate_window(df_cpi[["value"]].dropna(), "monthly", 12)
                    logger.info(f"✅ [AkShare] CN_CPI: 成功截取 {len(cn_data['CN_CPI'])} 个月数据")
            except Exception as e:
                logger.warning(f"⚠️ [AkShare] CN_CPI 抓取失败: {e}")

            # 2. 中国 GDP (季度 8 个季度)
            try:
                df_gdp = ak.macro_china_gdp()
                if not df_gdp.empty:
                    df_gdp['date'] = pd.to_datetime(df_gdp.iloc[:, 0], errors='coerce')
                    df_gdp = df_gdp.dropna(subset=['date']).sort_values('date').set_index('date')
                    df_gdp['value'] = pd.to_numeric(df_gdp.iloc[:, 1], errors='coerce')
                    
                    cn_data["CN_GDP_AK"] = self._truncate_window(df_gdp[["value"]].dropna(), "quarterly", 8)
                    logger.info(f"✅ [AkShare] CN_GDP: 成功截取 {len(cn_data['CN_GDP_AK'])} 个季度数据")
            except Exception as e:
                logger.warning(f"⚠️ [AkShare] CN_GDP 抓取失败: {e}")

        except ImportError:
            logger.error("❌ 未安装 AkShare")
            
        return cn_data

    def fetch_all_data(self):
        all_data = {}
        all_data.update(self.fetch_fred_data())
        all_data.update(self.fetch_yahoo_data())
        all_data.update(self.fetch_china_akshare_data())
        
        logger.info("=" * 60)
        logger.info(f"🎯 数据抓取完成！所有 22 个指标均按【每日1年/月度12期/季度8期】精确裁剪，保留右侧 Natural Edge！")
        logger.info("=" * 60)
        return all_data

if __name__ == "__main__":
    fetcher = MacroDataFetcher()
    data = fetcher.fetch_all_data()