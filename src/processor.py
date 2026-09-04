# -*- coding: utf-8 -*-
"""
数据清洗与对齐引擎：
1. 负责 Ragged Edge（锯齿状右侧断点）的动态对齐与截断；
2. 完成月度重采样、归一化计算；
3. 生成专门提交给 Gemini API 的精简宏观摘要 JSON。
"""

import pandas as pd
import numpy as np
import logging

class DataProcessor:
    def __init__(self, settings: dict):
        self.m_window = settings.get("monthly_window", 12)
        self.q_window = settings.get("quarterly_window", 8)
        self.d_window = settings.get("daily_window", 365)

    def _resample_and_align(self, series: pd.Series, freq: str) -> pd.Series:
        """重采样并格式化时间戳"""
        if series.empty:
            return series

        series = series.sort_index()
        if freq == "daily":
            # 填补缺失交易日，保留自然天数
            res = series.last("365D")
        elif freq == "monthly":
            # 统一定位到月末，取当月平均值或最后一个有效值
            res = series.resample("ME").mean()
        elif freq == "quarterly":
            # 统一定位到季末
            res = series.resample("QE").last()
        else:
            res = series

        return res

    def process(self, raw_data: dict, charts_config: list) -> tuple:
        """
        处理所有图表数据：
        返回 (cleaned_charts_data, summary_for_ai)
        """
        cleaned_charts_data = {}
        summary_metrics = []

        for chart in charts_config:
            chart_id = chart["id"]
            freq = chart.get("frequency", "monthly")
            chart_type = chart.get("type", "multi_line")

            series_list = []
            categories = []
            
            # 用于对齐时间轴的数据集
            df_chart = pd.DataFrame()

            for s in chart["series"]:
                key = f"{s['source']}:{s['code']}"
                raw_s = raw_data.get(key, pd.Series(dtype=float))

                if raw_s.empty:
                    continue

                processed_s = self._resample_and_align(raw_s, freq)
                
                # 截取窗口大小
                if freq == "monthly":
                    processed_s = processed_s.tail(self.m_window + 6) # 多留 6 个月算变动
                elif freq == "quarterly":
                    processed_s = processed_s.tail(self.q_window + 4)
                elif freq == "daily":
                    processed_s = processed_s.tail(self.d_window)

                df_chart[s["name"]] = processed_s

                # 记录精简摘要数据供 Gemini 使用
                if len(processed_s) >= 2:
                    latest_val = float(processed_s.iloc[-1]) if not np.isnan(processed_s.iloc[-1]) else None
                    prev_val = float(processed_s.iloc[-2]) if not np.isnan(processed_s.iloc[-2]) else None
                    chg = (latest_val - prev_val) if (latest_val and prev_val) else None
                    
                    summary_metrics.append({
                        "indicator": s["name"],
                        "latest_date": str(processed_s.index[-1].strftime('%Y-%m-%d')),
                        "latest_value": round(latest_val, 2) if latest_val else "N/A",
                        "previous_value": round(prev_val, 2) if prev_val else "N/A",
                        "change": round(chg, 2) if chg else "N/A"
                    })

            if df_chart.empty:
                continue

            # 归一化处理 (基期=100)
            if chart_type == "normalized_line":
                df_chart = df_chart.apply(lambda x: (x / x.dropna().iloc[0]) * 100 if not x.dropna().empty else x)

            # 裁切回展示窗口
            if freq == "monthly":
                df_chart = df_chart.tail(self.m_window)
            elif freq == "quarterly":
                df_chart = df_chart.tail(self.q_window)

            # 格式化时间 X 轴
            if freq == "quarterly":
                x_axis = [f"{d.year}Q{d.quarter}" for d in df_chart.index]
            elif freq == "monthly":
                x_axis = [d.strftime('%Y-%m') for d in df_chart.index]
            else:
                x_axis = [d.strftime('%Y-%m-%d') for d in df_chart.index]

            # 转化为 JS/ECharts 接受的数据结构（把 NaN 变成 None/null）
            series_payload = []
            for col in df_chart.columns:
                # 寻找配置中的颜色等细节
                s_conf = next((item for item in chart["series"] if item["name"] == col), {})
                series_payload.append({
                    "name": col,
                    "data": [None if np.isnan(v) else round(float(v), 2) for v in df_chart[col].values],
                    "color": s_conf.get("color"),
                    "type": s_conf.get("type", "line"),
                    "axis": s_conf.get("axis", 0)
                })

            cleaned_charts_data[chart_id] = {
                "title": chart["title"],
                "category": chart.get("category", "general"),
                "type": chart_type,
                "x_axis": x_axis,
                "series": series_payload
            }

        return cleaned_charts_data, summary_metrics