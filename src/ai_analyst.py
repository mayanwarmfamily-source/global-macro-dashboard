# -*- coding: utf-8 -*-
"""
Gemini AI 宏观分析引擎：
读取 processor 生成的精简数据摘要 JSON，
调用 Google GenAI API 生成穿透式全球宏观逻辑解读 HTML 文本。
"""

import json
import logging
import os
from google import genai

class GeminiMacroAnalyst:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key) if api_key else None

    def generate_analysis(self, summary_metrics: list, prompt_template: str) -> str:
        """调用 Gemini 生成 Markdown/HTML 穿透分析"""
        if not self.client:
            logging.warning("⚠️ 未检测到 GEMINI_API_KEY，跳过 AI 宏观解读生成。")
            return "<div class='ai-notice'>⚠️ GEMINI_API_KEY 未配置，宏观 AI 分析模块不可用。</div>"

        try:
            logging.info("🧠 正在请求 Gemini API 生成穿透式全球宏观分析报告...")
            
            # 将精简摘要转化为格式化 JSON 字符串
            summary_json_str = json.dumps(summary_metrics, ensure_ascii=False, indent=2)
            
            # 填入 Prompt
            full_prompt = prompt_template.format(data_summary=summary_json_str)

            # 调用最新 SDK API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )

            logging.info("✅ Gemini AI 分析报告成功生成！")
            return response.text

        except Exception as e:
            logging.error(f"❌ Gemini API 调用失败: {e}")
            return f"<div class='ai-error'>⚠️ AI 分析生成失败: {str(e)}</div>"