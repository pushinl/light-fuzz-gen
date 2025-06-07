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
    
    def save_harness(self, target_name, code, extension=".c"):
        """保存harness代码到文件
        
        Args:
            target_name: 目标名称，用于生成文件名
            code: 代码内容
            extension: 文件扩展名，默认为.c
        
        Returns:
            生成的文件路径
        """
        # 确保扩展名以点号开头
        if not extension.startswith("."):
            extension = f".{extension}"
            
        file_path = os.path.join(self.harness_dir, f"{target_name}_harness{extension}")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        return file_path
        
    def save_harness(self, target_name, code, language="c"):
        """保存多函数harness代码到文件
        
        Args:
            target_name: 目标名称，用于生成文件名
            code: 代码内容
            language: 编程语言，用于确定文件扩展名
        
        Returns:
            生成的文件路径
        """
        # 根据语言确定扩展名
        extension_map = {
            "c": ".c",
            "c++": ".cpp",
            "cpp": ".cpp",
            "python": ".py",
            "py": ".py",
            "java": ".java",
            "javascript": ".js",
            "js": ".js",
            "rust": ".rs"
        }
        
        extension = extension_map.get(language.lower(), ".c")
        return self.save_harness(target_name, code, extension) 