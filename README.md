# Light-Fuzz-Gen

A lightweight C/C++ program fuzzing harness generation tool based on large language models.

## Project Overview

Light-Fuzz-Gen is a tool that leverages large language models (such as GPT-3.5, GPT-4, etc.) to automatically generate Fuzzing Harness code. This tool automatically generates test cases suitable for fuzzing by providing target function signatures, parameter types, and return types.

## Directory Structure

```
light-fuzz-gen/
├── agent/                   # Agent module for handling interactions with large language models
│   ├── model.py             # Large model API interaction
│   ├── config.py            # Configuration file handling
│   ├── utils.py             # Utility functions
│   └── __init__.py          # Module initialization
├── benchmark-sets/          # Directory for target function configuration files
│   └── cups.yaml            # CUPS library related function configuration example
├── harness/                 # Output directory for generated Harness code
├── logs/                    # Log output directory
├── prompts/                 # Directory for prompt templates
├── main.py                  # Main program entry point
├── README.md                # Project documentation
├── .env                     # Environment variable configuration
└── .gitignore               # Git ignore configuration

```

## Usage

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables:

Create a `.env` file and add the following content:

```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional custom API
```

3. Run the program:

```bash
python main.py cups  # Use benchmark-sets/cups.yaml configuration file
```

## Configuration File Format

Create YAML format configuration files in the `benchmark-sets` directory, for example:

```yaml
"functions":
  - "name": "ippReadIO"
    "signature": "ipp_state_t ippReadIO(void *, ipp_io_cb_t, int, ipp_t *, ipp_t *);"
  - "name": "cupsFileOpen"
    "signature": "cups_file_t * cupsFileOpen(const char *, const char *);"
  - "name": "cupsFileClose"
    "signature": "int cupsFileClose(cups_file_t *);"
  - "name": "cupsFileRead"
    "signature": "ssize_t cupsFileRead(cups_file_t *fp, char *buf, size_t bytes);"
"additional": "When calling ippReadIO, you should use cupsFileRead in parameter list."
"language": "c"
"project": "cups"
"target_name": "fuzz_ipp_gen"
"target_repo": "https://github.com/OpenPrinting/cups"
"target_path": "/src/cups/ossfuzz/fuzz_ipp_gen.c"
"target_header_files": ["cups/ipp.h", "file.h"]
```

## Prompt Templates

Prompt templates are located in `prompts/`, which use `{placeholder}` format placeholders that will be replaced with actual function information.

## Multi-Function Processing

The system analyzes multiple functions in the configuration file, understands the relationships between them, and generates harness code that can reasonably call these functions:

1. The system automatically extracts all function information defined in the YAML file
2. Analyzes possible calling relationships between functions and generates a harness that can effectively test these functions
3. For functions with obvious calling relationships (such as initialization/processing/cleanup), the generated harness will call these functions in logical order

# Automated Agent Workflow

This agent workflow can automatically generate YAML configuration files for fuzzing from target C/C++ repositories.

## Features

1. **Automatic Code Analysis**: Scan C/C++ source code files in target repositories
2. **Function Extraction**: Use regular expressions and tree-sitter to extract function definitions and signatures
3. **Intelligent Analysis**: Call LLM to analyze function functionality, classification, and relationships
4. **Configuration Generation**: Automatically generate YAML configuration files that meet format requirements
5. **Batch Processing**: Support batch processing of large codebases

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage Methods

### Basic Usage

```bash
python run_agent.py cups-filters --project-name cups-filters --target-repo https://github.com/OpenPrinting/cups-filters
```

### Complete Parameters

```bash
python agent_workflow.py /path/to/repo \
    --project-name my-project \
    --target-repo https://github.com/user/repo \
    --api-key your-openai-key \
    --verbose
```

### Environment Variables

```bash
export OPENAI_API_KEY="your-api-key"
python run_agent.py cups-filters
```

## Workflow

```
1. 📁 Read Repository Code
   ├── Scan *.c, *.h, *.cpp, *.hpp files
   └── Filter invalid files

2. 🔍 Function Extraction
   ├── Use regular expressions to identify function definitions
   ├── Extract function names, signatures, location information
   └── Get function body content

3. 🤖 LLM Analysis
   ├── Analyze function functionality and purpose
   ├── Classify functions
   ├── Identify dependencies between functions
   └── Evaluate fuzzing value

4. 📝 YAML Generation
   ├── Group related functions by functionality
   ├── Design logical calling chains
   ├── Generate standard format YAML configurations
   └── Save to benchmark-sets/ directory
```

## Output Format

Generated YAML files follow this format:

```yaml
"functions":
  - "name": "function_name"
    "signature": "return_type function_name(parameters);"
"additional": "Brief description of function relationships"
"language": "c"
"project": "project-name"
"target_name": "fuzz_module_name"
"target_repo": "https://github.com/user/repo"
"target_path": "/src/project/ossfuzz/fuzz_module.c"
"target_header_files": ["header1.h", "header2.h"]
```

## Function Classification

The workflow automatically classifies functions into the following categories:

- `file_operations` - File operations
- `memory_management` - Memory management
- `string_processing` - String processing
- `network_communication` - Network communication
- `data_parsing` - Data parsing
- `error_handling` - Error handling
- `initialization_cleanup` - Initialization/cleanup
- `format_conversion` - Format conversion
- `configuration_management` - Configuration management
- `debug_logging` - Debug/logging
- `filter_processing` - Filter processing
- `printer_management` - Printer management

## Configuration Directory Structure

```
project/
├── prompts/                    # LLM prompt templates
│   ├── function_analysis.txt
│   ├── yaml_generation.txt
│   └── batch_function_analysis.txt
├── benchmark-sets/             # Generated YAML files
│   ├── project-category1.yaml
│   ├── project-category2.yaml
│   └── ...
├── agent_workflow.py           # Main workflow script
├── run_agent.py               # Simplified run script
└── requirements.txt           # Dependency list
```

## Advanced Usage

### Limit Number of Functions to Process

```bash
python run_agent.py repo-path --max-functions 20
```

### Custom Output Directory

```bash
python run_agent.py repo-path --output-dir custom-output
```

### Detailed Debug Information

```bash
python run_agent.py repo-path --verbose
```

### Analysis Only Without File Generation

```bash
python run_agent.py repo-path --dry-run
```

## Notes

1. **API Quota**: Using OpenAI API requires sufficient quota, large projects may consume many tokens
2. **Code Quality**: The workflow is mainly for standard C/C++ code, complex macro definitions may affect parsing
3. **Function Count**: It is recommended to process no more than 50 functions at a time to avoid exceeding LLM context limits
4. **Network Connection**: Requires stable network connection to access OpenAI API

## Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   Error: Please provide OpenAI API key
   Solution: Set OPENAI_API_KEY environment variable or use --api-key parameter
   ```

2. **No Functions Found**
   ```
   Error: No functions extracted
   Solution: Check code format, ensure function definitions conform to standard C syntax
   ```

3. **Empty Generated Files**
   ```
   Error: No YAML files generated
   Solution: Check function analysis results, may need to adjust classification thresholds
   ```

### Log Files

The workflow generates an `agent_workflow.log` log file containing detailed execution information.

## Example Output

Running example for cups-filters project:

```bash
$ python run_agent.py cups-filters --project-name cups-filters

2024-01-01 10:00:00 - INFO - Starting to process project: cups-filters
2024-01-01 10:00:01 - INFO - Read 45 source code files in total
2024-01-01 10:00:02 - INFO - Extracted 127 functions in total
2024-01-01 10:00:05 - INFO - Analyzing function batch 1/5
2024-01-01 10:00:15 - INFO - Starting to generate YAML files...
2024-01-01 10:00:16 - INFO - Generated YAML file: benchmark-sets/cups-filters-filter_processing.yaml
2024-01-01 10:00:16 - INFO - Generated YAML file: benchmark-sets/cups-filters-file_operations.yaml

✅ Successfully generated 8 YAML configuration files:
   📄 benchmark-sets/cups-filters-filter_processing.yaml
   📄 benchmark-sets/cups-filters-file_operations.yaml
   📄 benchmark-sets/cups-filters-format_conversion.yaml
   📄 benchmark-sets/cups-filters-memory_management.yaml
   📄 benchmark-sets/cups-filters-string_processing.yaml
   📄 benchmark-sets/cups-filters-error_handling.yaml
   📄 benchmark-sets/cups-filters-configuration_management.yaml
   📄 benchmark-sets/cups-filters-initialization_cleanup.yaml
```
