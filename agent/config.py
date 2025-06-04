import os
import yaml
import json

class ConfigHandler:
    def __init__(self, benchmark_dir, prompts_dir):
        self.benchmark_dir = benchmark_dir
        self.prompts_dir = prompts_dir
    
    def load_benchmark_config(self, benchmark_set):
        """加载benchmark配置文件"""
        config_path = os.path.join(self.benchmark_dir, f"{benchmark_set}.yaml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def load_prompt_template(self, template_name="multi_function_harness.txt"):
        """加载prompt模板"""
        template_path = os.path.join(self.prompts_dir, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def extract_functions_info(self, config):
        """从配置中提取所有函数的信息"""
        functions = []
        
        # 提取函数列表
        functions_list = config.get("functions", [])
        
        # 提取每个函数的信息
        for func in functions_list:
            function_info = {
                "name": func.get("name", "unknown"),
                "signature": func.get("signature", ""),
                "return_type": func.get("return_type", "void"),
            }
            
            # 处理参数信息
            if "params" in func:
                # 参数是详细的对象列表
                params = func["params"]
                param_types = [param.get("type", "void") for param in params]
                param_names = [param.get("name", f"param{i}") for i, param in enumerate(params)]
                function_info["param_types"] = param_types
                function_info["param_names"] = param_names
            
            # 添加包含文件
            function_info["includes"] = func.get("includes", [])
            
            functions.append(function_info)
        
        # 添加项目和语言信息
        project_info = {
            "project_name": config.get("project", "unknown"),
            "language": config.get("language", "c"),
            "target_name": config.get("target_name", "fuzz_target"),
            "target_path": config.get("target_path", ""),
            "functions": functions
        }
        
        return project_info
    
    def prepare_multi_function_prompt(self, template, project_info):
        """准备包含多个函数的prompt模板"""
        # 基本项目信息
        filled_template = template
        filled_template = filled_template.replace("{project_name}", project_info.get("project_name", "unknown"))
        filled_template = filled_template.replace("{language}", project_info.get("language", "c"))
        filled_template = filled_template.replace("{target_name}", project_info.get("target_name", "fuzz_target"))
        
        # 处理多个函数的信息
        functions = project_info.get("functions", [])
        
        # 创建函数列表的JSON字符串
        functions_json = json.dumps(functions, indent=2)
        filled_template = filled_template.replace("{functions_json}", functions_json)
        
        # 创建函数签名列表
        function_signatures = []
        for func in functions:
            function_signatures.append(func.get("signature", ""))
        
        filled_template = filled_template.replace("{function_signatures}", "\n".join(function_signatures))
        
        # 主函数名称（用于生成harness文件名）
        if functions:
            filled_template = filled_template.replace("{main_function_name}", functions[0].get("name", "unknown"))
        
        return filled_template 