#!/usr/bin/env python
"""
CLI tool to generate agent stubs from pipeline.yml
"""

import argparse
import sys
import traceback
from pathlib import Path
from typing import Dict, Any

from ruamel.yaml import YAML

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.core.prompt_intelligence_engine import PromptIntelligenceEngine
from topaz_agent_kit.cli.stubs.agents import UNIVERSAL_AGENT_TEMPLATE
from topaz_agent_kit.utils.agent_class_naming import AgentClassNaming


class AgentGenerator:
    """
    Generates agent stubs from pipeline.yml using Prompt Variables Intelligence Engine.
    Supports the new clean architecture with automatic variable detection.
    Uses universal template for all agent frameworks.
    """
    
    def __init__(self):
        self.logger = Logger("AgentGenerator")
        self.yaml_loader = YAML()
        self.yaml_loader.preserve_quotes = True
        self.yaml_loader.width = 4096
    
    
    def generate_agents(self, project_path: str | Path, overwrite: bool = False) -> int:
        """
        Generate agent stubs from pipeline.yml using new architecture.
        
        Args:
            project_path: Path to project root (contains config/pipeline.yml)
            overwrite: Whether to overwrite existing files
            
        Returns:
            0 on success, 1 on error
        """
        self.logger.info("Starting agent generation")
        
        try:
            # Initialize Prompt Intelligence Engine
            prompt_intelligence = PromptIntelligenceEngine()
            
            # Load pipeline config
            pipeline_file = Path(project_path).resolve() / "config" / "pipeline.yml"
            
            if not pipeline_file.exists():
                self.logger.error(f"Pipeline file not found: {pipeline_file}")
                return 1

            with open(pipeline_file, 'r', encoding='utf-8') as f:
                config = self.yaml_loader.load(f)

            # Get agents from flat structure
            agents = []
            pipeline_configs = {}  # Store pipeline configs for later use
            
            # Check if this is a multi-pipeline configuration with flat structure
            if "pipelines" in config:
                for pipeline in config["pipelines"]:
                    if isinstance(pipeline, dict) and "config_file" in pipeline:
                        pipeline_file = pipeline["config_file"]
                        pipeline_path = Path(project_path) / "config" / pipeline_file
                        
                        if pipeline_path.exists():
                            self.logger.input(f"Loading pipeline: {pipeline_file}")
                            with open(pipeline_path, 'r', encoding='utf-8') as f:
                                pipeline_config = self.yaml_loader.load(f)
                            
                            # Store pipeline config for later use (OS-agnostic path handling)
                            pipeline_id = pipeline.get("id", Path(pipeline_file).stem)
                            pipeline_configs[pipeline_id] = pipeline_config
                            
                            # Extract agents from this pipeline's nodes (using config_file)
                            if "nodes" in pipeline_config:
                                for node in pipeline_config["nodes"]:
                                    if isinstance(node, dict) and "config_file" in node:
                                        config_file = node["config_file"]
                                        # Load agent config from flat structure
                                        agent_config_path = Path(project_path) / "config" / config_file
                                        
                                        if agent_config_path.exists():
                                            with open(agent_config_path, 'r', encoding='utf-8') as f:
                                                agent_config = self.yaml_loader.load(f)
                                                # Extract agent_id from config_file path (OS-agnostic)
                                                agent_id = Path(config_file).stem
                                                # Add pipeline_id to agent config for context
                                                agent_config["_pipeline_id"] = pipeline_id
                                                agent_config["id"] = agent_id
                                                agents.append(agent_config)
                                        else:
                                            self.logger.warning(f"Agent config file not found: {agent_config_path}")
            else:
                self.logger.error("No pipelines found in pipeline.yml")
                return 1
            
            # Also check for independent agents in the flat structure
            if "independent_agents" in config:
                for agent in config["independent_agents"]:
                    if isinstance(agent, dict) and "config_file" in agent:
                        agent_config_path = Path(project_path) / "config" / agent["config_file"]
                        
                        if agent_config_path.exists():
                            with open(agent_config_path, 'r', encoding='utf-8') as f:
                                agent_config = self.yaml_loader.load(f)
                                # Independent agents don't belong to a specific pipeline
                                agent_config["_pipeline_id"] = None
                                agents.append(agent_config)
                        else:
                            self.logger.warning(f"Independent agent config file not found: {agent_config_path}")
            
            self.logger.info(f"Found {len(agents)} agents to generate")

            # Create base agents directory (flat structure)
            base_agents_dir = Path(project_path) / "agents"
            base_agents_dir.mkdir(parents=True, exist_ok=True)

            # Generate agent files
            for agent_config in agents:
                agent_id = agent_config.get("id")
                agent_type = agent_config.get("type")
                
                if not agent_id:
                    self.logger.warning("Agent missing 'id' field, skipping: {}", agent_config)
                    continue

                if not agent_type:
                    self.logger.warning("Agent missing 'type' field, skipping: {}", agent_config)
                    continue
                
                # Analyze agent configuration
                self.logger.debug(f"Analyzing {agent_type} agent: {agent_id}")
                
                # Get the correct pipeline config for this agent (if it belongs to a pipeline)
                pipeline_id = agent_config.get("_pipeline_id")
                if pipeline_id and pipeline_id in pipeline_configs:
                    # Multi-pipeline: use individual pipeline config
                    pipeline_config = pipeline_configs[pipeline_id]
                    pipeline_structure = {
                        "agents": [a.get("id") for a in agents if a.get("_pipeline_id") == pipeline_id],
                        "pattern": pipeline_config.get("pattern", {})
                    }
                elif pipeline_id is None:
                    # Independent agent - no pipeline structure
                    pipeline_structure = {
                        "agents": [agent_id],
                        "pattern": {}
                    }
                else:
                    self.logger.error(f"Agent {agent_id} has invalid pipeline_id: {pipeline_id}")
                    continue
                
                # Create agent context for context-aware variable classification
                agent_context = {
                    "agent_id": agent_id,
                    "agent_config": agent_config,
                    "pipeline_structure": pipeline_structure
                }
                
                analysis = prompt_intelligence.analyze_agent_config(agent_config, project_path, agent_context)
                
                # Validate agent type and get framework mappings
                try:
                    type_prefix, framework_name = AgentClassNaming.get_framework_info(agent_type)
                    base_agent_class = f"{type_prefix}BaseAgent"
                    class_name = AgentClassNaming.generate_class_name(agent_id)
                except ValueError as e:
                    self.logger.warning(f"Unknown agent type '{agent_type}' for agent '{agent_id}': {e}")
                    continue
                
                # Use universal template for all frameworks
                template = UNIVERSAL_AGENT_TEMPLATE

                # Write agent file (flat structure)
                module_name = AgentClassNaming.generate_module_name(agent_id)
                agent_file = base_agents_dir / f"{module_name}.py"
                
                if agent_file.exists() and not overwrite:
                    self.logger.info(f"Agent file exists, skipping: {agent_file}")
                    continue
                    
                # Generate code using Prompt Variables Intelligence Engine
                try:
                    self.logger.info(f"  Generating code for {agent_type} agent: {agent_id}")
                    
                    agent_variables_code = prompt_intelligence.generate_agent_variables_code(analysis, agent_context)
                    
                    self.logger.debug(f"  Generated variables code: {len(agent_variables_code)} chars")
                    
                    # Format the universal template with framework-specific data using safe string replacement
                    self.logger.debug(f"  Formatting universal template for {agent_type} framework")
                    formatted_template = template.replace("{{BaseAgentClass}}", base_agent_class)
                    formatted_template = formatted_template.replace("{{FrameworkName}}", framework_name)
                    formatted_template = formatted_template.replace("{{ClassName}}", class_name)
                    formatted_template = formatted_template.replace("{{agent_variables_code}}", agent_variables_code)
                    
                    self.logger.debug(f"  Template formatted successfully: {len(formatted_template)} chars")
                    
                    # Write the generated agent file
                    with open(agent_file, 'w', encoding='utf-8') as f:
                        f.write(formatted_template)
                    
                    self.logger.success(f"Generated {agent_type} agent: {agent_file}")
                    
                    # Log analysis results
                    self.logger.debug(f"  - Variables detected: {len(analysis['variables'])}")
                    self.logger.debug(f"  - Custom variables: {analysis['custom_variables']}")
                    self.logger.debug(f"  - Generation hints: {analysis['generation_hints']}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to generate agent {agent_id}: {e}")
                    self.logger.error(f"Full traceback: {traceback.format_exc()}")
                    return 1

            self.logger.success(f"Successfully generated {len(agents)} agents")
            return 0
            
        except Exception as e:
            self.logger.error(f"Agent generation failed: {e}")
            traceback.print_exc()
            return 1


def main() -> None:
    """CLI entry point for agent generation"""
    parser = argparse.ArgumentParser(description="Generate agent stubs from YAML config")
    parser.add_argument("project", help="Path to project root (contains config/pipeline.yml)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    generator = AgentGenerator()
    exit_code = generator.generate_agents(args.project, args.overwrite)
    sys.exit(exit_code)


if __name__ == "__main__":
    main() 