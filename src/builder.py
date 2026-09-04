# -*- coding: utf-8 -*-
"""
静态网页构建器：
读取 config.yaml 配置、DataProcessor 清洗后的图表 JSON 与 Gemini AI 生成的分析报告，
使用 Jinja2 模板引擎编译生成 public/index.html，作为静态部署产物。
"""

import os
import json
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

class SiteBuilder:
    def __init__(self, template_dir: str = "templates", output_dir: str = "public"):
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.env = Environment(loader=FileSystemLoader(self.template_dir))

    def build(self, config: dict, charts_data: dict, ai_analysis_html: str):
        """编译渲染 index.html"""
        logging.info("🔨 开始编译构建 HTML 静态页面...")

        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        template = self.env.get_template("index.html")

        # 准备数据上下文
        context = {
            "settings": config.get("settings", {}),
            "charts": charts_data,
            "ai_analysis": ai_analysis_html,
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 渲染生成 HTML 内容
        rendered_html = template.render(context)

        # 写入 public/index.html
        output_path = os.path.join(self.output_dir, "index.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        logging.info(f"🎉 静态面板页面已成功生成 -> {output_path}")