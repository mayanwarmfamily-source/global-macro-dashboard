import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiMacroAnalyst:
    def __init__(self, api_key=None):
        # 优先使用传入的 api_key，若无则从环境变量 GEMINI_API_KEY 读取
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # 使用标准的 gemini-1.5-flash 模型，兼顾分析速度与质量
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY 未找到，AI 自动分析功能将被跳过。")

    def generate_summary(self, summary_metrics):
        """
        根据传入的宏观数据指标生成简明扼要的宏观经济摘要。
        """
        if not self.model:
            return "AI 分析未启用：未检测到有效 API 密钥。"

        if not summary_metrics:
            return "当前暂无足够的宏观数据用于分析。"

        # 构建发送给 AI 的提示词
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