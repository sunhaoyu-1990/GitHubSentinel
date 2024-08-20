# src/llm.py

import os
from openai import OpenAI


class LLM:
    def __init__(self):
        self.client = OpenAI()

    def generate_daily_report(self, markdown_content, dry_run=False):
        system_prompt = f"你是一名报告和简报编写专家，尤其擅长和了解开源项目的最新进展方面的内容。下面会输入一些项目的最新进展，你需要根据输入内容，按照功能合并同类项，同时按照你的理解以重要程度进行各大块内部各内容的排序，生成一份中文简报，报告排班要清晰，要求每一部分不能自己忽略内容，要全面体现输入的内容，报告内容至少包括如下内容：1）新增的功能；2）主要改进；3）修复问题；4)亮点内容"
        user_prompt = f"输入内容如下：\n{markdown_content}"
        if dry_run:
            with open("daily_progress/prompt.txt", "w+") as f:
                f.write(system_prompt)
                f.write(user_prompt)
            return "DRY RUN"

        print("Before call GPT")
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        print("After call GPT")
        print(response)
        return response.choices[0].message.content
