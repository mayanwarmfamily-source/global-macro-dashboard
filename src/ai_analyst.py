import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiMacroAnalyst:
    def __init__(self, api_key=None, model_name=None, settings=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name or "gemini-1.5-flash"
        self.settings = settings or {}

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.error(f"初始化 Gemini 模型失败: {e}")
                self.model = None
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY 未找到，跳过 AI 分析。")

    def generate_analysis(self, summary_metrics=None, prompt_template=None, *args, **kwargs):
        """根据宏观数据指标生成 AI 分析内容"""
        if not self.model:
            return "AI 分析未启用：未检测到有效 API 密钥。"

        if not summary_metrics:
            return "当前暂无足够的宏观数据用于分析。"

        # 如果 main.py 传了提示词模板就优先使用，否则用默认模板
        if prompt_template:
            try:
                prompt = prompt_template.format(summary_metrics=summary_metrics)
            except Exception:
                prompt = f"{prompt_template}\n\n数据指标：\n{summary_metrics}"
        else:
            prompt = f"""
你是一位顶尖的全球宏观经济学家。请根据以下最新的宏观经济与金融指标数据，提供一份简明扼要、逻辑严密的市场洞察报告（字数控制在 200-300 字以内）：

最新数据指标：
{summary_metrics}

要求：
1. 总结当前全球主要经济体（美、中、欧等）的增长、通胀与利率环境。
2. 简要分析主要资产类别（美股、美债收益率、黄金、商品等）的潜在风险与机会。
3. 语言使用专业中文，排版结构清晰，直接输出分析结论即可。
"""

        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            return "AI 未能生成有效的分析文本。"
        except Exception as e:
            logger.error(f"调用 Gemini API 生成分析时出错: {e}")
            return f"生成 AI 宏观分析时发生错误: {str(e)}"