import os
import time

class Logger:
    def __init__(self, logs_dir):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
    
    def log(self, target, stage, content):
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_content = f"\n[{timestamp}][Stage: {stage}]\n{content}\n"
        
        # 写入日志文件
        with open(os.path.join(self.logs_dir, f"{target}.log"), "a", encoding="utf-8") as f:
            f.write(log_content)
        
        # 输出到控制台
        print(f"\n[{timestamp}][Stage: {stage}]\n{content}\n")

class FileHandler:
    def __init__(self, harness_dir):
        self.harness_dir = harness_dir
        os.makedirs(harness_dir, exist_ok=True)
    
    def save_harness(self, target_name, code, language="c"):
        """保存harness代码到文件
        
        Args:
            target_name: 目标名称，用于生成文件名
            code: 代码内容
            language: 文件语言，默认为.c
        
        Returns:
            生成的文件路径
        """
            
        file_path = os.path.join(self.harness_dir, f"{target_name}.{language}")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        return file_path