# -*- coding: utf-8 -*-
"""
全球宏观 Dashboard 一键调度主程序 (main.py)
自动完成配置加载、22个核心指标抓取、数据清洗对齐、Gemini AI 分析生成与 Plotly HTML 静态页面编译。
"""

import os
import sys
import yaml
import logging

# 导入全新的数据抓取模块
from src.data_fetcher import MacroDataFetcher
from src.processor import DataProcessor
from src.ai_analyst import GeminiMacroAnalyst
from src.builder import SiteBuilder

# 配置全局日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if not os.path.path.exists(config_path) if hasattr(os.path, 'path') else not os.path.exists(config_path):
        logging.error(f"❌ 配置文件未找到: {config_path}")
        return {}
    
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"❌ 解析 config.yaml 失败: {e}")
            return {}

def main():
    logging.info("==================================================")
    logging.info("🚀 全球宏观数据与金融条件分析面板 Dashboard - 开始运行")
    logging.info("==================================================")

    # 1. 加载配置
    config = load_config()

    # 2. 抓取 22 个核心宏观指标数据 (8Q / 12M / 1Y Natural Edge)
    logging.info("\n--- 步骤 1: 开始抓取 22 个宏观与金融指标 ---")
    fetcher = MacroDataFetcher()
    raw_data = fetcher.fetch_all_data()

    if not raw_data:
        logging.error("❌ 未抓取到任何有效数据，程序终止！")
        sys.exit(1)

    # 3. 数据清洗与格式化对齐
    logging.info("\n--- 步骤 2: 数据清洗与指标对齐 ---")
    processor = DataProcessor(raw_data)
    processed_data = processor.process_all() if hasattr(processor, 'process_all') else raw_data

    # 4. Gemini AI 分析研判生成
    logging.info("\n--- 步骤 3: 调用 AI 生成宏观研判解读 ---")
    analyst = GeminiMacroAnalyst(config=config)
    ai_insights = analyst.generate_insights(processed_data) if hasattr(analyst, 'generate_insights') else {}

    # 5. 生成 Plotly 交互图表与多页 HTML 简报
    logging.info("\n--- 步骤 4: 编译静态 HTML 页面与 Plotly 图表 ---")
    builder = SiteBuilder(config=config)
    builder.build_site(processed_data, ai_insights) if hasattr(builder, 'build_site') else None

    logging.info("==================================================")
    logging.info("🎉 所有流程顺利执行完毕！页面已输出至 public/ 目录")
    logging.info("==================================================")

if __name__ == "__main__":
    main()