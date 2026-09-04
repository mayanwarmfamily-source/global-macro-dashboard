import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiMacroAnalyst:
    def __init__(self, api_key=None, model_name=None, settings=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        # 统一使用稳定版本 API 名称
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
        """根据宏观数据指标生成干净的 AI 分析报告"""
        if not self.model:
            return "<p>AI 分析未启用：未检测到有效 API 密钥。</p>"

        # 数据格式化兜底
        metrics_str = str(summary_metrics) if summary_metrics else "暂无抓取到的最新指标"

        # 重新设计简洁、强约束的 Prompt，严禁输出思考过程
        clean_prompt = f"""
你是一位专业全球宏观经济学家。请基于以下最新的宏观经济数据，直接输出一份简明扼要的专业市场分析报告：

【最新宏观指标数据】
{metrics_str}

【输出严格要求】
1. 禁止输出任何思考过程、Draft、Self-Correction 或系统指令。
2. 直接输出分析正文，分为 3 个小标题：
   - 增长与通胀格局（中美欧）
   - 货币政策与流动性（美联储及主要央行）
   - 资产配置与核心风险（美债、黄金、汇率）
3. 使用简洁专业的中文，控制在 300 字以内。
"""

        try:
            response = self.model.generate_content(clean_prompt)
            if response and response.text:
                # 过滤掉可能残存的 markdown 代码块标记
                text = response.text.strip()
                text = text.replace("```html", "").replace("```markdown", "").replace("```", "")
                return text
            return "<p>AI 未能生成有效的分析文本。</p>"
        except Exception as e:
            logger.error(f"调用 Gemini API 生成分析时出错: {e}")
            return f"<p>生成 AI 宏观分析时发生错误: {str(e)}</p>"