import os
import sys
import yaml
from dotenv import load_dotenv
from agent import ModelAgent, ConfigHandler, Logger, FileHandler

# Load environment variables
load_dotenv()

# Define directory constants
LOGS_DIR = "logs"
PROMPTS_DIR = "prompts"
BENCHMARKS_DIR = "benchmark-sets"
HARNESS_DIR = "harness"

# Prompt template filename
PROMPT_TEMPLATE = "c-repository.txt"

def generate_harness(benchmark_config: dict, config_handler: ConfigHandler, model_agent: ModelAgent, logger: Logger, file_handler: FileHandler):
	"""Process multiple related functions in the configuration simultaneously"""

	prompt_template = config_handler.load_prompt_template(PROMPT_TEMPLATE)
	
	# Extract all function information
	project_info = config_handler.extract_functions_info(benchmark_config)
	target_name = project_info.get("target_name", "fuzz_target")
	
	logger.log(target_name, "Start Processing", f"Processing project: {project_info.get('project_name')} multiple functions")
	
	# Prepare prompt
	filled_prompt = config_handler.prepare_prompt(prompt_template, project_info)
	logger.log(target_name, "Generated Prompt", filled_prompt)
	
	# Call large model API
	response = model_agent.call_api(filled_prompt, model_name="gpt-4o", temperature=0.4)
	logger.log(target_name, "Model Response", response if response else "API call failed")
	
	if response:
		# Extract solution code from response
		harness_code = model_agent.extract_solution_from_response(response)
		logger.log(target_name, "Extracted Code", harness_code if harness_code else "Failed to extract code")
		
		if harness_code:
			# Save harness code to file
			language = project_info.get("language", "c")
			harness_file_path = file_handler.save_harness(target_name, harness_code, language)
			logger.log(target_name, "Complete", f"Harness code saved to {harness_file_path}")
		else:
			logger.log(target_name, "Failed", "Failed to extract valid code from response")
	else:
		logger.log(target_name, "Failed", "API call failed, no response received")


def main():
	# Check command line arguments
	if len(sys.argv) < 2:
		print("Usage: python main.py <benchmark-set>")
		exit(1)
	
	# Get benchmark set name
	benchmark_set = sys.argv[1]
	
	# Create tool instances
	config_handler = ConfigHandler(BENCHMARKS_DIR, PROMPTS_DIR)
	model_agent = ModelAgent()
	logger = Logger(LOGS_DIR)
	file_handler = FileHandler(HARNESS_DIR)
	
	try:
		# Load benchmark configuration
		benchmark_config = config_handler.load_benchmark_config(benchmark_set)
		
		generate_harness(benchmark_config, config_handler, model_agent, logger, file_handler)
		
	except FileNotFoundError as e:
		print(f"Error: {str(e)}")
		exit(1)
	except Exception as e:
		print(f"Error occurred during processing: {str(e)}")
		exit(1)

if __name__ == "__main__":
	main()
