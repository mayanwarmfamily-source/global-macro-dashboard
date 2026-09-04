import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self, raw_data, charts_config):
        self.raw_data = raw_data
        self.charts_config = charts_config

    def process():
        pass

def process(raw_data, charts_config):
    cleaned_charts = {}
    summary_metrics = {}

    for chart_id, config in charts_config.items():
        series_list = []
        for series_cfg in config.get('series', []):
            s_id = series_cfg.get('id')
            if s_id in raw_data and not raw_data[s_id].empty:
                s = raw_data[s_id].copy()
                s.name = series_cfg.get('name', s_id)
                series_list.append(s)

        if not series_list:
            continue

        df = pd.concat(series_list, axis=1).sort_index()
        
        # 填充缺失值并做前向/后向填充
        df = df.ffill().bfill()

        # 取近 365 天的数据（用兼容新版 pandas 的切片逻辑替换 .last()）
        if isinstance(df.index, pd.DatetimeIndex) and len(df) > 0:
            cutoff_date = df.index[-1] - pd.Timedelta(days=365)
            df = df[df.index >= cutoff_date]

        # 整理图表数据结构
        cleaned_charts[chart_id] = {
            'title': config.get('title', chart_id),
            'type': config.get('type', 'line'),
            'labels': df.index.strftime('%Y-%m-%d').tolist(),
            'datasets': [
                {
                    'label': col,
                    'data': [None if np.isnan(v) else round(float(v), 4) for v in df[col].values]
                } for col in df.columns
            ]
        }

        # 记录最新的关键摘要指标
        if not df.empty:
            last_row = df.iloc[-1]
            for col in df.columns:
                val = last_row[col]
                if not np.isnan(val):
                    summary_metrics[col] = round(float(val), 2)

    return cleaned_charts, summary_metrics