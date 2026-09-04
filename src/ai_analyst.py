import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiMacroAnalyst:
    def __init__(self, api_key=None, model_name=None, settings=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        # 如果你有指定的模型名称可以写在这里，比如 gemini-1.5-flash
        self.model_name = model_name or "gemini-1.5-flash"
        self.settings = settings or {}

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.error(f"初始化 API 模型失败: {e}")
                self.model = None
        else:
            self.model = None
            logger.warning("未找到 GEMINI_API_KEY，跳过 AI 分析。")

    def generate_analysis(self, summary_metrics=None, prompt_template=None, *args, **kwargs):
        """根据宏观数据指标生成 AI 分析内容"""
        if not self.model:
            return "AI 分析未启用：未检测到有效 API 密钥。"

        # 如果数据为空，给出一个基本的情况说明，而不是直接弹暂无数据
        metrics_text = summary_metrics if summary_metrics else "部分 FRED 指标抓取受限，仅基于当前已获取的基础市场趋势分析。"

        if prompt_template:
            try:
                prompt = prompt_template.format(summary_metrics=metrics_text)
            except Exception:
                prompt = f"{prompt_template}\n\n数据指标：\n{metrics_text}"
        else:
            prompt = f"""
你是一位顶尖的全球宏观经济学家。请基于以下宏观数据与市场背景，生成一份简明扼要的市场解读（200字左右）：

数据情况：
{metrics_text}

请总结当前全球主要经济体环境及资产走向。
"""

        try:
            response = self.model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            return "AI 未能生成有效的分析文本。"
        except Exception as e:
            logger.error(f"调用 API 生成分析时出错: {e}")
            return f"生成 AI 宏观分析时发生错误: {str(e)}"