import os
import sys
import yaml
from dotenv import load_dotenv
from agent import ModelAgent, ConfigHandler, Logger, FileHandler

# 加载环境变量
load_dotenv()

# 定义目录常量
LOGS_DIR = "logs"
PROMPTS_DIR = "prompts"
BENCHMARKS_DIR = "benchmark-sets"
HARNESS_DIR = "harness"

# 提示模板文件名
PROMPT_TEMPLATE = "c-repository.txt"

def generate_harness(benchmark_config: dict, config_handler: ConfigHandler, model_agent: ModelAgent, logger: Logger, file_handler: FileHandler):
	"""同时处理配置中的多个相关函数"""

	prompt_template = config_handler.load_prompt_template(PROMPT_TEMPLATE)
	
	# 提取所有函数信息
	project_info = config_handler.extract_functions_info(benchmark_config)
	target_name = project_info.get("target_name", "fuzz_target")
	
	logger.log(target_name, "开始处理", f"处理项目: {project_info.get('project_name')} 的多个函数")
	
	# 准备prompt
	filled_prompt = config_handler.prepare_prompt(prompt_template, project_info)
	logger.log(target_name, "生成的Prompt", filled_prompt)
	
	# 调用大模型API
	response = model_agent.call_api(filled_prompt, model_name="gpt-4o", temperature=0.4)
	logger.log(target_name, "大模型响应", response if response else "API调用失败")
	
	if response:
		# 从响应中提取solution代码
		harness_code = model_agent.extract_solution_from_response(response)
		logger.log(target_name, "提取的代码", harness_code if harness_code else "未能提取代码")
		
		if harness_code:
			# 保存harness代码到文件
			language = project_info.get("language", "c")
			harness_file_path = file_handler.save_harness(target_name, harness_code, language)
			logger.log(target_name, "完成", f"Harness代码已保存到 {harness_file_path}")
		else:
			logger.log(target_name, "失败", "未能从响应中提取有效代码")
	else:
		logger.log(target_name, "失败", "API调用失败，未获取到响应")


def main():
	# 检查命令行参数
	if len(sys.argv) < 2:
		print("Usage: python main.py <benchmark-set>")
		exit(1)
	
	# 获取benchmark集合名称
	benchmark_set = sys.argv[1]
	
	# 创建工具实例
	config_handler = ConfigHandler(BENCHMARKS_DIR, PROMPTS_DIR)
	model_agent = ModelAgent()
	logger = Logger(LOGS_DIR)
	file_handler = FileHandler(HARNESS_DIR)
	
	try:
		# 加载benchmark配置
		benchmark_config = config_handler.load_benchmark_config(benchmark_set)
		
		generate_harness(benchmark_config, config_handler, model_agent, logger, file_handler)
		
	except FileNotFoundError as e:
		print(f"错误: {str(e)}")
		exit(1)
	except Exception as e:
		print(f"处理过程中发生错误: {str(e)}")
		exit(1)

if __name__ == "__main__":
	main()
