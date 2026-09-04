# -*- coding: utf-8 -*-
"""
全球宏观 Dashboard 一键调度主程序 (main.py)
自动完成配置加载、多源数据抓取、数据清洗对齐、Gemini AI 分析生成与 HTML 静态页面编译。
"""

import os
import sys
import yaml
import logging

from src.fetcher import DataFetcher
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
    if not os.path.exists(config_path):
        logging.error(f"❌ 配置文件未找到: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    logging.info("==================================================")
    logging.info("🚀 全球宏观与金融条件分析面板 Dashboard - 开始运行")
    logging.info("==================================================")

    # 1. 加载 YAML 配置
    config = load_config()
    settings = config.get("settings", {})
    charts_config = config.get("charts", [])
    ai_config = config.get("ai_analyst", {})

    # 2. 读取环境变量中的 API Key
    fred_api_key = os.getenv("FRED_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not fred_api_key:
        logging.warning("⚠️ 提示: 未检测到 FRED_API_KEY 环境变量，部分 FRED 序列可能无法获取。")
    if not gemini_api_key:
        logging.warning("⚠️ 提示: 未检测到 GEMINI_API_KEY 环境变量，AI 宏观分析报告将跳过生成。")

    # 3. 初始化并运行数据抓取引擎
    fetcher = DataFetcher(fred_api_key=fred_api_key)
    raw_data = fetcher.fetch_all(charts_config)

    # 4. 初始化并运行数据清洗与对齐引擎
    processor = DataProcessor(settings=settings)
    cleaned_charts, summary_metrics = processor.process(raw_data, charts_config)

    # 5. 调用 Gemini 2.5 宏观分析引擎
    ai_analyst = GeminiMacroAnalyst(
        api_key=gemini_api_key,
        model_name=ai_config.get("model", "gemini-2.5-flash")
    )
    prompt_template = ai_config.get("prompt_template", "")
    ai_analysis_html = ai_analyst.generate_analysis(summary_metrics, prompt_template)

    # 6. 构建并导出 HTML 静态页面
    builder = SiteBuilder()
    builder.build(
        config=config,
        charts_data=cleaned_charts,
        ai_analysis_html=ai_analysis_html
    )

    logging.info("==================================================")
    logging.info("✨ 所有流程顺利执行完毕！产物已输出至 public/index.html")
    logging.info("==================================================")

if __name__ == "__main__":
    main()