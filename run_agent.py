#!/usr/bin/env python3
"""
Agent workflow run script - Simplified version

Usage example:
python run_agent.py cups-filters --project-name cups-filters --target-repo https://github.com/OpenPrinting/cups-filters

Optional parameters:
--api-key: OpenAI API key (or set environment variable OPENAI_API_KEY)
--output-dir: Output directory (default: benchmark-sets)
--max-functions: Maximum number of functions to process (default: 30)
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv
from pathlib import Path
from agent_workflow import AgentWorkflow

def setup_logging(verbose=False):
    """Setup logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('agent_workflow.log')
        ]
    )

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent workflow - Generate fuzzing YAML configurations from repository")
    parser.add_argument("repo_path", help="Target repository path")
    parser.add_argument("--project-name", help="Project name")
    parser.add_argument("--target-repo", help="Target repository URL")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--output-dir", default="benchmark-sets", help="Output directory")
    parser.add_argument("--max-functions", type=int, default=30, help="Maximum number of functions to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Analysis only without file generation")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Check API key
    load_dotenv()
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("Please provide OpenAI API key (via --api-key parameter or OPENAI_API_KEY environment variable)")
        sys.exit(1)
    
    # Check repository path
    if not os.path.exists(args.repo_path):
        logger.error(f"Repository path does not exist: {args.repo_path}")
        sys.exit(1)
    
    # Set project name
    project_name = args.project_name or os.path.basename(args.repo_path.rstrip('/'))
    
    logger.info(f"Starting to process project: {project_name}")
    logger.info(f"Repository path: {args.repo_path}")
    logger.info(f"Output directory: {args.output_dir}")
    
    try:
        # Create workflow
        workflow = AgentWorkflow(api_key=api_key)
        
        # Run workflow
        generated_files = workflow.run(
            repo_path=args.repo_path,
            project_name=project_name,
            target_repo=args.target_repo or f"https://github.com/user/{project_name}"
        )
        
        # Output results
        if generated_files:
            print(f"\n[SUCCESS] Successfully generated {len(generated_files)} YAML configuration files:")
            for file_path in generated_files:
                print(f"   [FILE] {file_path}")
            
            print(f"\n[STATS] Statistics:")
            print(f"   - Project name: {project_name}")
            print(f"   - Generated files: {len(generated_files)}")
            print(f"   - Output directory: {args.output_dir}")
            
        else:
            print("[ERROR] No YAML files generated")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("User interrupted operation")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
