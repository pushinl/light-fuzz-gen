import os
import re
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

class ModelAgent:
    def __init__(self, api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL):
        self.model = OpenAI(api_key=api_key, base_url=base_url)
    
    def call_api(self, prompt, model_name="gpt-4o", temperature=0.4):
        """调用大模型API并获取响应"""
        try:
            response = self.model.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates code for fuzzing."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用API出错: {str(e)}")
            return None
    
    def extract_markdown_code(self, response_text):
        """从响应中提取markdown代码块"""
        if not response_text:
            return None
        
        pattern = r'```[\w\s]*\n([\s\S]*?)```'
        matches = re.findall(pattern, response_text)
        if matches:
            return matches[0]
        return None
    
    def extract_solution_from_response(self, response_text):
        """从响应中提取solution字段的代码"""
        if not response_text:
            return None
            
        # 尝试解析XML格式的solution
        solution_pattern = r'<solution>([\s\S]*?)</solution>'
        solution_match = re.search(solution_pattern, response_text)
        
        if solution_match:
            solution_content = solution_match.group(1)
            code = self.extract_markdown_code(solution_content)
            if code:
                return code
            return solution_content
        
        # 如果没有XML格式，直接尝试提取markdown代码块
        code = self.extract_markdown_code(response_text)
        if code:
            return code
        
        # 如果都没有匹配到，返回整个响应
        return response_text 