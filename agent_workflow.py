#!/usr/bin/env python3
"""
Automated Agent Workflow: Generate YAML configuration files from target repositories

This script can:
1. Read C/C++ source code from target repositories
2. Use tree-sitter to extract function definitions and signatures
3. Call LLM to analyze function functionality and classification
4. Generate YAML configuration files and save to benchmark-sets directory
"""

import os
import sys
import json
import yaml
import fnmatch
import argparse
import logging
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
import re
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Function:
    """Function information data class"""
    name: str
    signature: str
    file_path: str
    start_line: int
    end_line: int
    body: str = ""
    summary: str = ""
    category: str = ""

@dataclass
class AnalysisResult:
    """LLM analysis result"""
    summary: str
    category: str
    dependencies: List[str]
    related_functions: List[str]

class CodeExtractor:
    """Code extractor - using regular expressions as fallback solution"""
    
    def __init__(self):
        # Regular expression pattern for C function definitions
        self.function_pattern = re.compile(
            r'^\s*(?:static\s+|inline\s+|extern\s+)?'  # Optional storage class specifiers
            r'(?:const\s+)?'                           # Optional const
            r'([a-zA-Z_]\w*(?:\s*\*)*)\s+'             # Return type
            r'([a-zA-Z_]\w*)\s*'                       # Function name
            r'\(([^)]*)\)\s*'                          # Parameter list
            r'(?:__attribute__\s*\([^)]*\)\s*)?'       # Optional attributes
            r'\{',                                     # Function body start
            re.MULTILINE
        )
        
        # C language keywords and common non-function identifiers
        self.c_keywords = {
            # C language keywords
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while',
            # C99 keywords
            'inline', 'restrict', '_Bool', '_Complex', '_Imaginary',
            # Common preprocessor and compiler related
            'define', 'include', 'ifdef', 'ifndef', 'endif', 'pragma',
            # Common types and identifiers
            'NULL', 'true', 'false', 'bool', 'size_t', 'ssize_t', 'uint8_t', 'uint16_t', 
            'uint32_t', 'uint64_t', 'int8_t', 'int16_t', 'int32_t', 'int64_t',
            # Single character or too short identifiers
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            # Common macros and built-in functions
            'MIN', 'MAX', 'ABS', 'TRUE', 'FALSE'
        }
    
    def extract_functions_regex(self, content: str, file_path: str) -> List[Function]:
        """Extract function definitions using regular expressions"""
        functions = []
        lines = content.split('\n')
        
        for match in self.function_pattern.finditer(content):
            return_type = match.group(1).strip()
            func_name = match.group(2).strip()
            params = match.group(3).strip()
            
            # Skip keywords, macro definitions or incomplete matches
            if (func_name.lower() in self.c_keywords or 
                func_name.isupper() or 
                len(func_name) < 2 or
                func_name.isdigit() or
                func_name[0].isdigit() or  # C identifiers cannot start with digits
                not func_name.replace('_', '').isalnum()):
                continue
            
            # Build function signature
            signature = f"{return_type} {func_name}({params});"
            
            # Get function line number in file
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            
            # Try to find the end position of function body
            brace_count = 1
            pos = match.end() - 1  # Start from the first {
            end_pos = pos
            
            while pos < len(content) and brace_count > 0:
                pos += 1
                if pos < len(content):
                    if content[pos] == '{':
                        brace_count += 1
                    elif content[pos] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = pos
                            break
            
            end_line = content[:end_pos].count('\n') + 1
            
            # Extract function body
            body = content[match.start():end_pos + 1]
            
            function = Function(
                name=func_name,
                signature=signature,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                body=body
            )
            functions.append(function)
            
        return functions

class RepositoryReader:
    """Repository code reader"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.extractor = CodeExtractor()
    
    def read_source_files(self, file_patterns: List[str] = None) -> List[Tuple[str, str]]:
        """Read source code files"""
        if file_patterns is None:
            file_patterns = ['*.c', '*.h', '*.cpp', '*.hpp']
        
        source_files = []
        
        for root, _, filenames in os.walk(self.repo_path):
            for pattern in file_patterns:
                for filename in fnmatch.filter(filenames, pattern):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        relative_path = os.path.relpath(file_path, self.repo_path)
                        source_files.append((relative_path, content))
                    except Exception as e:
                        logger.warning(f"Unable to read file {file_path}: {e}")
        
        logger.info(f"Read {len(source_files)} source code files in total")
        return source_files
    
    def extract_functions(self, source_files: List[Tuple[str, str]]) -> List[Function]:
        """Extract functions from source code files"""
        all_functions = []
        
        for file_path, content in source_files:
            try:
                functions = self.extractor.extract_functions_regex(content, file_path)
                all_functions.extend(functions)
                logger.info(f"Extracted {len(functions)} functions from {file_path}")
            except Exception as e:
                logger.error(f"Failed to extract functions from {file_path}: {e}")
        
        logger.info(f"Extracted {len(all_functions)} functions in total")
        return all_functions

class LLMAnalyzer:
    """LLM analyzer"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = model
        self.prompts_dir = Path("prompts")
    
    def load_prompt(self, prompt_name: str) -> str:
        """Load prompt file"""
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding='utf-8')
        else:
            logger.warning(f"Prompt file does not exist: {prompt_file}")
            return ""
    
    def analyze_function(self, function: Function) -> AnalysisResult:
        """Analyze a single function"""
        prompt = f"""
Please analyze the functionality of the following C language function:

Function name: {function.name}
Signature: {function.signature}
File: {function.file_path}

Function body summary:
{function.body[:1000]}...

Please provide:
1. Functionality summary (one sentence)
2. Function classification (e.g.: file operations, memory management, network communication, data parsing, etc.)
3. Dependencies on other functions (if apparent)
4. Related functions (functions in the same category)

Please return in JSON format:
{{
    "summary": "functionality summary",
    "category": "function classification", 
    "dependencies": ["dependency function 1", "dependency function 2"],
    "related_functions": ["related function 1", "related function 2"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # try parse JSON response
            try:
                result_json = json.loads(result_text)
                return AnalysisResult(
                    summary=result_json.get("summary", ""),
                    category=result_json.get("category", "unknown"),
                    dependencies=result_json.get("dependencies", []),
                    related_functions=result_json.get("related_functions", [])
                )
            except json.JSONDecodeError:
                # If JSON parsing fails, return basic information
                return AnalysisResult(
                    summary=f"Function {function.name} in {function.file_path}",
                    category="unknown",
                    dependencies=[],
                    related_functions=[]
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze function {function.name}: {e}")
            return AnalysisResult(
                summary=f"Function {function.name}",
                category="unknown", 
                dependencies=[],
                related_functions=[]
            )
    
    def batch_analyze_functions(self, functions: List[Function], max_batch_size: int = 5) -> Dict[str, AnalysisResult]:
        """Batch analyze functions to avoid exceeding context limits"""
        results = {}
        
        for i in range(0, len(functions), max_batch_size):
            batch = functions[i:i + max_batch_size]
            logger.info(f"Analyzing function batch {i//max_batch_size + 1}/{(len(functions) + max_batch_size - 1)//max_batch_size}")
            
            for function in batch:
                results[function.name] = self.analyze_function(function)
        
        return results

class YAMLGenerator:
    """YAML configuration file generator"""
    
    def __init__(self, llm_analyzer: LLMAnalyzer):
        self.llm_analyzer = llm_analyzer
        self.output_dir = Path("benchmark-sets")
        self.output_dir.mkdir(exist_ok=True)
    
    def group_functions_by_category(self, functions: List[Function], 
                                  analysis_results: Dict[str, AnalysisResult]) -> Dict[str, List[Function]]:
        """Group functions by category"""
        categories = {}
        
        for function in functions:
            result = analysis_results.get(function.name)
            if result:
                category = result.category
                if category not in categories:
                    categories[category] = []
                categories[category].append(function)
        
        return categories
    
    def generate_yaml_for_category(self, category: str, functions: List[Function], 
                                 analysis_results: Dict[str, AnalysisResult],
                                 project_info: Dict[str, str]) -> Dict:
        """Generate YAML configuration for specific category"""
        yaml_functions = []
        additional_info = []
        
        for function in functions[:6]:  # Limit each YAML to maximum 6 functions
            result = analysis_results.get(function.name)
            yaml_functions.append({
                "name": function.name,
                "signature": function.signature
            })
            if result and result.summary:
                additional_info.append(f"{function.name}: {result.summary}")
        
        # Infer header files
        header_files = set()
        for function in functions:
            if function.file_path.endswith('.h'):
                header_files.add(function.file_path.replace('/', '/').split('/')[-1])
        
        # If no obvious header files, add common header files
        if not header_files:
            header_files = {"stdio.h", "stdlib.h", "string.h"}
        
        yaml_config = {
            "functions": yaml_functions,
            "additional": "; ".join(additional_info[:3]),  # Limit additional info length
            "language": project_info.get("language", "c"),
            "project": project_info.get("project", "unknown"),
            "target_name": f"fuzz_{category.lower().replace(' ', '_')}",
            "target_repo": project_info.get("target_repo", ""),
            "target_path": f"/src/{project_info.get('project', 'unknown')}/ossfuzz/fuzz_{category.lower().replace(' ', '_')}.c",
            "target_header_files": list(header_files)
        }
        
        return yaml_config
    
    def clean_signature(self, signature: str) -> str:
        """Clean function signature, handle newline and format issues"""
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', signature.strip())
        # Remove tabs and newlines
        cleaned = cleaned.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Normalize spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned
    
    def generate_yaml_files(self, functions: List[Function], 
                          analysis_results: Dict[str, AnalysisResult],
                          project_info: Dict[str, str]) -> List[str]:
        """Generate YAML configuration files"""
        categories = self.group_functions_by_category(functions, analysis_results)
        generated_files = []
        
        for category, category_functions in categories.items():
            if len(category_functions) < 2:  # Skip categories with only one function
                continue
            
            yaml_config = self.generate_yaml_for_category(
                category, category_functions, analysis_results, project_info
            )
            
            # Generate unique filename to avoid overwriting
            safe_category = re.sub(r'[^a-zA-Z0-9_-]', '_', category.lower())
            
            # If category is empty or invalid, use timestamp to generate unique name
            if not safe_category or safe_category == '_' or safe_category == '':
                timestamp = time.strftime("%H%M%S")
                rand_num = random.randint(100, 999)
                safe_category = f"category_{timestamp}_{rand_num}"
            
            # Ensure filename uniqueness
            base_filename = f"{project_info.get('project', 'unknown')}-{safe_category}"
            filename = f"{base_filename}.yaml"
            filepath = self.output_dir / filename
            
            # If file already exists, add sequence number
            counter = 1
            while filepath.exists():
                filename = f"{base_filename}_{counter}.yaml"
                filepath = self.output_dir / filename
                counter += 1
            
            # Save YAML file
            try:
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write('"functions":\n')
                    for func in yaml_config["functions"]:
                        # Clean newlines in signature
                        clean_sig = self.clean_signature(func["signature"])
                        f.write(f'  - "name": "{func["name"]}"\n')
                        f.write(f'    "signature": "{clean_sig}"\n')
                    
                    f.write(f'"additional": "{yaml_config["additional"]}"\n')
                    f.write(f'"language": "{yaml_config["language"]}"\n')
                    f.write(f'"project": "{yaml_config["project"]}"\n')
                    f.write(f'"target_name": "{yaml_config["target_name"]}"\n')
                    f.write(f'"target_repo": "{yaml_config["target_repo"]}"\n')
                    f.write(f'"target_path": "{yaml_config["target_path"]}"\n')
                    f.write(f'"target_header_files": {json.dumps(yaml_config["target_header_files"])}\n')
                generated_files.append(str(filepath))
                logger.info(f"Generated YAML file: {filepath}")
                
            except Exception as e:
                logger.error(f"Failed to save YAML file {filepath}: {e}")
        
        return generated_files

class AgentWorkflow:
    """Main agent workflow class"""
    
    def __init__(self, api_key: str = None):
        self.reader = None
        self.analyzer = LLMAnalyzer(api_key)
        self.generator = YAMLGenerator(self.analyzer)
    
    def run(self, repo_path: str, project_name: str = None, target_repo: str = "") -> List[str]:
        """Run complete workflow"""
        logger.info(f"Starting to process repository: {repo_path}")
        
        # 1. Read repository code
        self.reader = RepositoryReader(repo_path)
        source_files = self.reader.read_source_files()
        
        if not source_files:
            logger.error("No source code files found")
            return []
        
        # 2. Extract functions
        functions = self.reader.extract_functions(source_files)
        
        if not functions:
            logger.error("No functions extracted")
            return []
        
        # Limit function count to avoid exceeding API limits
        if len(functions) > 50:
            functions = functions[:50]
            logger.info(f"Limited function count to {len(functions)}")
        
        # 3. Analyze functions
        logger.info("Starting LLM analysis...")
        analysis_results = self.analyzer.batch_analyze_functions(functions)
        
        # 4. Generate YAML files
        if not project_name:
            project_name = os.path.basename(repo_path.rstrip('/'))
        
        project_info = {
            "project": project_name,
            "language": "c",
            "target_repo": target_repo or f"https://github.com/user/{project_name}"
        }
        
        logger.info("Starting to generate YAML files...")
        generated_files = self.generator.generate_yaml_files(functions, analysis_results, project_info)
        
        logger.info(f"Workflow completed, generated {len(generated_files)} YAML files")
        return generated_files

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Automated agent workflow: Generate YAML configuration files from target repository")
    parser.add_argument("repo_path", help="Target repository path")
    parser.add_argument("--project-name", help="Project name (default uses directory name)")
    parser.add_argument("--target-repo", help="Target repository URL")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check repository path
    if not os.path.exists(args.repo_path):
        logger.error(f"Repository path does not exist: {args.repo_path}")
        sys.exit(1)
    
    # Create workflow instance
    workflow = AgentWorkflow(args.api_key)
    
    try:
        # Run workflow
        generated_files = workflow.run(
            repo_path=args.repo_path,
            project_name=args.project_name,
            target_repo=args.target_repo or ""
        )
        
        print("\nGenerated YAML files:")
        for file_path in generated_files:
            print(f"  - {file_path}")
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()