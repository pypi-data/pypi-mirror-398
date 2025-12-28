#!/usr/bin/env python
"""
CLI tool to generate service stubs for remote agents from pipeline.yml
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

from ruamel.yaml import YAML

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.cli.stubs.services.remote_agent_service import (
    SINGLE_PROTOCOL_SERVICE_TEMPLATE,
    MULTI_PROTOCOL_SERVICE_TEMPLATE,
    INDIVIDUAL_SERVICE_TEMPLATE,
    PIPELINE_SERVICE_TEMPLATE,
    UNIFIED_SERVICE_TEMPLATE,
    UNIFIED_A2A_SERVER_TEMPLATE,
)
from topaz_agent_kit.utils.agent_class_naming import AgentClassNaming
from urllib.parse import urlparse


class ServiceGenerator:
    """
    Generates service stubs for remote agents from pipeline.yml.
    Provides extensible framework for service generation.
    """

    def __init__(self):
        self.logger = Logger("ServiceGenerator")
        self.yaml_loader = YAML()
        self.yaml_loader.preserve_quotes = True
        self.yaml_loader.width = 4096

    def _parse_url_and_port(self, url: str) -> tuple[str, int]:
        """
        Parse URL to extract host and port

        Args:
            url: Full URL string (e.g., "http://127.0.0.1:8091")

        Returns:
            Tuple of (host, port)

        Raises:
            ValueError: If URL is missing hostname or port
        """
        parsed = urlparse(url)
        if parsed.hostname is None:
            raise ValueError(f"URL '{url}' missing hostname")
        if parsed.port is None:
            raise ValueError(f"URL '{url}' missing port number")
        return parsed.hostname, parsed.port

    def _extract_path_from_url(self, url: str) -> str:
        """Extract path from URL for logging purposes"""
        parsed = urlparse(url)
        return parsed.path or "/"

    def generate_services(
        self, project_path: str | Path, overwrite: bool = False
    ) -> int:
        """
        Generate service stubs for remote agents from pipeline.yml

        Args:
            project_path: Path to project root (contains config/pipeline.yml)
            overwrite: Whether to overwrite existing files

        Returns:
            0 on success, 1 on error
        """
        self.logger.info("Starting service generation")

        project_path = Path(project_path).resolve()
        pipeline_file = project_path / "config" / "pipeline.yml"

        if not pipeline_file.exists():
            self.logger.error(f"Pipeline file not found: {pipeline_file}")
            return 1

        # Load pipeline config
        with open(pipeline_file, "r", encoding='utf-8') as f:
            config = self.yaml_loader.load(f)

        # Get agents from flat structure
        agents = []
        pipeline_configs = {}  # Store pipeline configs for later use

        # Check if this is a multi-pipeline configuration with flat structure
        if "pipelines" in config:
            for pipeline in config["pipelines"]:
                if isinstance(pipeline, dict) and "config_file" in pipeline:
                    pipeline_file = pipeline["config_file"]
                    pipeline_path = project_path / "config" / pipeline_file

                    if pipeline_path.exists():
                        self.logger.input(f"Loading pipeline: {pipeline_file}")
                        with open(pipeline_path, "r", encoding='utf-8') as f:
                            pipeline_config = self.yaml_loader.load(f)

                        # Store pipeline config for later use (OS-agnostic path handling)
                        pipeline_id = pipeline.get(
                            "id", Path(pipeline_file).stem
                        )
                        pipeline_configs[pipeline_id] = pipeline_config

                        # Extract agents from this pipeline's nodes (using config_file)
                        if "nodes" in pipeline_config:
                            for node in pipeline_config["nodes"]:
                                if isinstance(node, dict) and "config_file" in node:
                                    config_file = node["config_file"]
                                    # Load agent config from flat structure
                                    agent_config_path = (
                                        project_path / "config" / config_file
                                    )

                                    if agent_config_path.exists():
                                        with open(agent_config_path, "r", encoding='utf-8') as f:
                                            agent_config = self.yaml_loader.load(f)
                                            # Extract agent_id from config_file path (OS-agnostic)
                                            agent_id = Path(config_file).stem
                                            # Add pipeline_id to agent config for context
                                            agent_config["_pipeline_id"] = pipeline_id
                                            agent_config["id"] = agent_id
                                            agents.append(agent_config)
                                            self.logger.debug(f"Added agent {agent_id} with _pipeline_id={pipeline_id}")
                                    else:
                                        self.logger.warning(
                                            f"Agent config file not found: {agent_config_path}"
                                        )
        else:
            self.logger.error("No pipelines found in pipeline.yml")
            return 1

        # Also check for independent agents in the flat structure
        if "independent_agents" in config:
            for agent in config["independent_agents"]:
                if isinstance(agent, dict) and "config_file" in agent:
                    agent_config_path = project_path / "config" / agent["config_file"]

                    if agent_config_path.exists():
                        with open(agent_config_path, "r", encoding='utf-8') as f:
                            agent_config = self.yaml_loader.load(f)
                            # Independent agents don't belong to a specific pipeline
                            agent_config["_pipeline_id"] = None
                            agents.append(agent_config)
                    else:
                        self.logger.warning(
                            f"Independent agent config file not found: {agent_config_path}"
                        )

        self.logger.info(f"Found {len(agents)} agents to check for remote services")

        # Create base services directory
        base_services_dir = project_path / "services"
        base_services_dir.mkdir(parents=True, exist_ok=True)

        # Get project package name
        project_pkg = project_path.name.replace("-", "_")

        # Identify agents that are part of unified A2A servers (multiple agents sharing same A2A port)
        # This is used to skip A2A startup code in individual service files
        agents_in_unified_servers = set()
        if pipeline_configs:
            for pipeline_id, pipeline_config in pipeline_configs.items():
                pipeline_agents = [a for a in agents if a.get("_pipeline_id") == pipeline_id and a.get("remote")]
                # Group by A2A port
                a2a_port_groups = {}
                for agent_config in pipeline_agents:
                    remote = agent_config.get("remote", {})
                    url = remote.get("url")
                    if url:
                        _, port = self._parse_url_and_port(url)
                        if port not in a2a_port_groups:
                            a2a_port_groups[port] = []
                        a2a_port_groups[port].append(agent_config.get("id"))
                # Agents in ports with multiple agents are part of unified servers
                for port, agent_ids in a2a_port_groups.items():
                    if len(agent_ids) > 1:
                        agents_in_unified_servers.update(agent_ids)
                        self.logger.debug(f"Agents {agent_ids} in pipeline {pipeline_id} share A2A port {port} - will use unified server")
        
        if agents_in_unified_servers:
            self.logger.info(f"Agents in unified A2A servers: {sorted(agents_in_unified_servers)}")

        # Generate service files for remote agents
        for agent_config in agents:
            # NEW: Remote is enabled by presence of config, not enabled flag
            remote = agent_config.get("remote", {})
            if not remote:
                self.logger.debug(
                    f"Skipping agent {agent_config.get('id')}: no remote configuration"
                )
                continue

            agent_id = agent_config.get("id")
            agent_type = (agent_config.get("type")).lower()

            # Get URL from remote config
            url = remote.get("url")
            if not url:
                self.logger.warning(
                    f"Agent {agent_id} has no URL configured in remote.url, skipping"
                )
                continue

            self.logger.debug(
                f"Processing service for agent: id={agent_id}, type={agent_type}, url={url}"
            )

            # Generate class names using centralized utility
            try:
                class_name = AgentClassNaming.generate_class_name(agent_id)
                module_name = AgentClassNaming.generate_module_name(agent_id)
            except ValueError as e:
                self.logger.warning(
                    f"Unsupported agent type '{agent_type}' for agent '{agent_id}': {e}"
                )
                continue

            # Flat structure: all services go directly in base services directory
            pipeline_id = agent_config.get("_pipeline_id")
            services_dir = base_services_dir  # Always use base services directory
            agent_module_path = module_name  # Flat structure - just the module name, template adds "agents." prefix

            # Generate service file
            service_file = services_dir / f"{agent_id}_service.py"

            if service_file.exists() and not overwrite:
                self.logger.debug(f"Skipping existing service file: {service_file}")
                continue

            self.logger.debug(
                f"Generating service for agent: id={agent_id}, type={agent_type}"
            )

            # Skip A2A agents that are part of unified servers
            if agent_id in agents_in_unified_servers:
                self.logger.debug(
                    f"Skipping individual service file for {agent_id}: A2A agent handled by unified server"
                )
                continue
            
            # Parse URL and extract port/path
            host, port = self._parse_url_and_port(url)
            path = self._extract_path_from_url(url)

            # Generate A2A service content
            formatted_content = self._process_service_template(
                SINGLE_PROTOCOL_SERVICE_TEMPLATE,
                project_pkg=project_pkg,
                agent_module_path=agent_module_path,
                class_name=class_name,
                agent_id=agent_id,
                protocol="a2a",
                port=port,
            )
            
            # For independent agents (no pipeline_id), replace 'service' with '{agent_id}_service'
            # so unified_service.py can import it correctly
            if not pipeline_id:
                # Replace variable declaration from 'service =' to '{agent_id}_service ='
                formatted_content = formatted_content.replace(
                    'service = BaseAgentService(',
                    f'{agent_id}_service = BaseAgentService('
                )
                # Replace template's 'service.' calls
                import re
                # Replace 'service.' that's not part of a longer variable name
                formatted_content = re.sub(
                    r'\bservice\.',
                    f'{agent_id}_service.',
                    formatted_content
                )

            with open(service_file, "w", encoding='utf-8') as f:
                f.write(formatted_content.strip())

            self.logger.debug(
                f"Generated A2A service for {agent_id}: {service_file}"
            )

        # Generate unified service file if multiple agents with different ports
        self._generate_unified_service(
            agents, base_services_dir, project_pkg, pipeline_configs, overwrite
        )

        self.logger.success("Service generation completed successfully")
        return 0

    def _process_service_template(self, template_str: str, **kwargs) -> str:
        """
        Process service template with custom variable substitution

        Args:
            template_str: Template string to process
            **kwargs: Variables to substitute

        Returns:
            Processed template string

        Raises:
            ValueError: If required variables are missing
        """
        # Define required variables for each template type
        if "SINGLE_PROTOCOL_SERVICE_TEMPLATE" in template_str:
            required_vars = [
                "agent_module_path",
                "class_name",
                "agent_id",
                "protocol",
                "port",
            ]
        elif "MULTI_PROTOCOL_SERVICE_TEMPLATE" in template_str:
            required_vars = [
                "agent_module_path",
                "class_name",
                "agent_id",
                "protocol_startup_code",
            ]
        elif "INDIVIDUAL_SERVICE_TEMPLATE" in template_str:
            required_vars = [
                "agent_import",
                "service_instance",
                "agent_startup_code",
                "agent_id",
            ]
        elif "PIPELINE_SERVICE_TEMPLATE" in template_str:
            required_vars = ["agent_imports", "agent_startup_code", "pipeline_id"]
        elif "UNIFIED_SERVICE_TEMPLATE" in template_str:
            required_vars = ["agent_imports", "service_instances", "agent_startup_code"]
        else:
            # Fallback: check for all possible variables in template
            required_vars = []
            all_vars = [
                "project_pkg",
                "agent_module_path",
                "class_name",
                "agent_id",
                "protocol",
                "port",
                "startup_code",
                "protocol_startup_code",
                "agent_imports",
                "service_instances",
                "agent_startup_code",
                "pipeline_id",
            ]
            for var in all_vars:
                if f"{{{var}}}" in template_str:
                    required_vars.append(var)

        # Validate required variables - fail fast
        missing_vars = []
        for var in required_vars:
            if (
                var not in kwargs
                or kwargs[var] is None
                or (isinstance(kwargs[var], str) and not kwargs[var].strip())
            ):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required variables for service template: {missing_vars}"
            )

        result = template_str

        # Replace variables (no defaults - all must be provided)
        result = result.replace("{project_pkg}", kwargs.get("project_pkg", ""))
        result = result.replace(
            "{agent_module_path}", kwargs.get("agent_module_path", "")
        )
        result = result.replace("{class_name}", kwargs.get("class_name", ""))
        result = result.replace("{agent_id}", kwargs.get("agent_id", ""))
        result = result.replace("{protocol}", kwargs.get("protocol", ""))
        result = result.replace("{port}", str(kwargs.get("port", "")))
        result = result.replace("{startup_code}", kwargs.get("startup_code", ""))
        result = result.replace(
            "{protocol_startup_code}", kwargs.get("protocol_startup_code", "")
        )
        result = result.replace("{agent_import}", kwargs.get("agent_import", ""))
        result = result.replace("{agent_imports}", kwargs.get("agent_imports", ""))
        result = result.replace(
            "{service_instance}", kwargs.get("service_instance", "")
        )
        result = result.replace(
            "{service_instances}", kwargs.get("service_instances", "")
        )
        result = result.replace(
            "{agent_startup_code}", kwargs.get("agent_startup_code", "")
        )
        result = result.replace("{pipeline_id}", kwargs.get("pipeline_id", ""))

        return result

    def _process_unified_a2a_template(self, template_str: str, **kwargs) -> str:
        """
        Process unified A2A server template with custom variable substitution

        Args:
            template_str: Template string to process
            **kwargs: Variables to substitute

        Returns:
            Processed template string
        """
        result = template_str
        result = result.replace("{service_imports}", kwargs.get("service_imports", ""))
        result = result.replace("{app_build_code}", kwargs.get("app_build_code", ""))
        result = result.replace("{mount_routes}", kwargs.get("mount_routes", ""))
        result = result.replace("{pipeline_id}", kwargs.get("pipeline_id", ""))
        a2a_port = str(kwargs.get("a2a_port", ""))
        result = result.replace("{a2a_port}", a2a_port)
        agent_list = kwargs.get("agent_list", "[]")
        result = result.replace("{agent_list}", agent_list)
        result = result.replace("{first_service_name}", kwargs.get("first_service_name", ""))
        # Calculate agent count from agent_list
        agent_count = len(eval(agent_list)) if agent_list else 0
        result = result.replace("{agent_count}", str(agent_count))
        # Convert Jinja2 escaped braces to single braces ({{ -> {, }} -> })
        result = result.replace("{{", "{")
        result = result.replace("}}", "}")
        return result

    def _generate_unified_service(
        self,
        agents: list,
        services_dir: Path,
        project_pkg: str,
        pipeline_configs: dict = None,
        overwrite: bool = False,
    ) -> None:
        """Generate a unified service file that runs all agents together"""
        # NEW: Filter agents that have remote configuration (implicit enablement)
        remote_agents = []
        for agent_config in agents:
            remote = agent_config.get("remote") or {}
            if remote:  # Remote is enabled by presence of config
                remote_agents.append(agent_config)

        # Only generate unified service if we have multiple agents
        if len(remote_agents) < 2:
            return

        # Generate agent imports and service instances
        agent_imports = []
        service_instances = []
        agent_startup_code = []

        for agent_config in remote_agents:
            agent_id = agent_config.get("id")
            agent_type = (agent_config.get("type")).lower()
            remote = agent_config.get("remote", {})
            url = remote.get("url")
            
            if not url:
                self.logger.warning(f"Agent {agent_id} has no URL configured, skipping")
                continue

            # Generate class names using centralized utility
            try:
                class_name = AgentClassNaming.generate_class_name(agent_id)
                module_name = AgentClassNaming.generate_module_name(agent_id)
            except ValueError as e:
                self.logger.warning(
                    f"Unsupported agent type '{agent_type}' for agent '{agent_id}': {e}"
                )
                continue

            # Add import (without agents. prefix since agents/ is added to sys.path directly)
            agent_imports.append(f"from {module_name} import {class_name}")

            # Get pipeline ID for directory structure
            pipeline_id = agent_config.get("_pipeline_id")
            # Use original agent name (no prefixing needed with unique names)
            service_agent_id = agent_id

            # Add service instance
            service_instances.append(f"""
# {agent_id} service ({pipeline_id})
{service_agent_id}_service = BaseAgentService(
    agent_id="{service_agent_id}",
    agent_class={class_name},
    project_path=Path(__file__).resolve().parents[1]
)""")

            # Add startup code for A2A server
            host, port = self._parse_url_and_port(url)
            path = self._extract_path_from_url(url)
            agent_startup_code.append(
                f"            {service_agent_id}_service.start_a2a_server(port={port}, path='{path}'),"
            )

        # Generate pipeline-level services for multi-pipeline configurations
        if pipeline_configs:
            self.logger.info(f"Generating pipeline services for {len(pipeline_configs)} pipelines")
            for pipeline_id, pipeline_config in pipeline_configs.items():
                try:
                    # Get agents for this pipeline from remote_agents (they already have remote config)
                    pipeline_agents = [
                        a for a in remote_agents if a.get("_pipeline_id") == pipeline_id
                    ]
                    if not pipeline_agents:
                        self.logger.debug(f"No agents found for pipeline {pipeline_id}")
                        continue

                    # Create pipeline-specific imports and services (unused but kept for compatibility)
                    pipeline_agent_imports = []
                    pipeline_service_instances = []
                    pipeline_agent_startup_code = []

                    # Generate pipeline service file (flat structure - no pipeline-specific directories)

                    # Generate individual service files first
                    individual_service_imports = []
                    individual_service_startup_calls = []
                    
                    # Initialize a2a_port_groups for unified server grouping
                    a2a_port_groups = {}
                    service_instances_for_unified = []

                    for agent_config in pipeline_agents:
                        agent_id = agent_config.get("id")
                        agent_type = (agent_config.get("type")).lower()
                        remote = agent_config.get("remote", {})

                        if not remote:
                            continue

                        url = remote.get("url")
                        if not url:
                            self.logger.warning(f"Agent {agent_id} has no URL configured, skipping")
                            continue

                        # Generate class names using centralized utility
                        try:
                            class_name = AgentClassNaming.generate_class_name(agent_id)
                            module_name = AgentClassNaming.generate_module_name(agent_id)
                        except ValueError as e:
                            self.logger.warning(
                                f"Unsupported agent type '{agent_type}' for agent '{agent_id}': {e}"
                            )
                            continue

                        # Generate individual service file
                        individual_service_file = services_dir / f"{agent_id}_service.py"

                        # Check if service file already exists (agent might be used in multiple pipelines)
                        if individual_service_file.exists() and not overwrite:
                            self.logger.debug(
                                f"Service file already exists for agent {agent_id} (used in multiple pipelines), skipping generation"
                            )
                            # Still add import for pipeline service (service instance already exists)
                            service_name = f"{agent_id}_service"
                            individual_service_imports.append(
                                f"from {agent_id}_service import {service_name}"
                            )
                            # Still need to track this service for unified server grouping
                            host, port = self._parse_url_and_port(url)
                            path = self._extract_path_from_url(url)
                            if port not in a2a_port_groups:
                                a2a_port_groups[port] = []
                            # Check if agent already added to avoid duplicates
                            agent_already_added = any(
                                a["agent_id"] == agent_id for a in a2a_port_groups[port]
                            )
                            if not agent_already_added:
                                a2a_port_groups[port].append({
                                    "agent_id": agent_id,
                                    "service_name": service_name,
                                    "path": path,
                                    "host": host
                                })
                                if service_name not in service_instances_for_unified:
                                    service_instances_for_unified.append(service_name)
                            continue

                        # Create individual service startup code (A2A only)
                        individual_startup_code = []
                        host, port = self._parse_url_and_port(url)
                        path = self._extract_path_from_url(url)
                        # Use agent_id only for service name (no pipeline prefix - services are shared across pipelines)
                        service_name = f"{agent_id}_service"
                        individual_startup_code.append(
                            f"            {service_name}.start_a2a_server(port={port}, path='{path}'),"
                        )

                        individual_startup_code_str = "\n".join(individual_startup_code)

                        # Generate individual service content
                        individual_formatted_content = self._process_service_template(
                            INDIVIDUAL_SERVICE_TEMPLATE,
                            agent_import=f"from {module_name} import {class_name}",
                            service_instance=f"""
# {agent_id} service
{service_name} = BaseAgentService(
    agent_id="{agent_id}",
    agent_class={class_name},
    project_path=Path(__file__).resolve().parents[1]
)""",
                            agent_startup_code=individual_startup_code_str,
                            agent_id=agent_id,
                        )

                        with open(individual_service_file, "w", encoding='utf-8') as f:
                            f.write(individual_formatted_content.strip())

                        self.logger.debug(
                            f"Generated individual service file: {individual_service_file}"
                        )

                        # Add import for pipeline service (need service instances, not just startup functions)
                        individual_service_imports.append(
                            f"from {agent_id}_service import {service_name}"
                        )
                        
                        # Track this service for unified server grouping (if not already added)
                        if service_name not in service_instances_for_unified:
                            service_instances_for_unified.append(service_name)
                            if port not in a2a_port_groups:
                                a2a_port_groups[port] = []
                            # Check if agent already added to avoid duplicates
                            agent_already_added = any(
                                a["agent_id"] == agent_id for a in a2a_port_groups[port]
                            )
                            if not agent_already_added:
                                a2a_port_groups[port].append({
                                    "agent_id": agent_id,
                                    "service_name": service_name,
                                    "path": path,
                                    "host": host
                                })

                    # Generate pipeline service file
                    pipeline_service_file = services_dir / f"{pipeline_id}_service.py"
                    
                    # Build pipeline service content
                    if not individual_service_imports:
                        self.logger.warning(
                            f"No individual service imports for pipeline {pipeline_id}, skipping pipeline service generation"
                        )
                        continue
                    
                    pipeline_agent_imports_str = "\n".join(individual_service_imports)
                    
                    # Generate unified A2A servers for each port group with multiple agents
                    unified_a2a_functions = []
                    individual_a2a_code = []
                    
                    self.logger.debug(f"Processing A2A port groups for {pipeline_id}: {list(a2a_port_groups.keys())}")
                    for port, agents in a2a_port_groups.items():
                        if len(agents) > 1:
                            # Multiple agents share this port - create unified server
                            app_build_lines = []
                            mount_routes = []
                            agent_list = [f'"{a["agent_id"]}"' for a in agents]
                            first_service = agents[0]["service_name"]
                            
                            for agent in agents:
                                app_build_lines.append(
                                    f"    {agent['agent_id']}_app = {agent['service_name']}.a2a_service.a2a_app.build()"
                                )
                                # Ensure path ends with /
                                mount_path = agent['path'] if agent['path'].endswith('/') else agent['path'] + '/'
                                mount_routes.append(
                                    f'        Mount("{mount_path}", app={agent["agent_id"]}_app),'
                                )
                            
                            # Process template and remove duplicate imports (they're in pipeline service content)
                            unified_function = self._process_unified_a2a_template(
                                UNIFIED_A2A_SERVER_TEMPLATE,
                                service_imports="",  # Imports are already in pipeline_agent_imports_str
                                app_build_code="\n".join(app_build_lines),
                                mount_routes="\n".join(mount_routes),
                                pipeline_id=pipeline_id,
                                a2a_port=port,
                                agent_list=f"[{', '.join(agent_list)}]",
                                first_service_name=first_service,
                            )
                            # Remove duplicate imports from unified template (already in pipeline service content)
                            # The template has imports at the top, but pipeline service content already has them
                            lines = unified_function.split('\n')
                            filtered_lines = []
                            in_import_section = True
                            for line in lines:
                                stripped = line.strip()
                                # Skip import statements, path setup, and empty lines at the start
                                if in_import_section:
                                    if (stripped.startswith('from ') or stripped.startswith('import ') or 
                                        stripped.startswith('sys.path') or stripped.startswith('# Add ') or
                                        stripped == ''):
                                        continue
                                    else:
                                        in_import_section = False
                                if not in_import_section:
                                    filtered_lines.append(line)
                            unified_a2a_functions.append('\n'.join(filtered_lines))
                        else:
                            # Single agent on this port - start normally
                            agent = agents[0]
                            individual_a2a_code.append(
                                f"            {agent['service_name']}.start_a2a_server(port={port}, path='{agent['path']}'),"
                            )
                    
                    # Combine all startup code
                    all_startup_code = []
                    if unified_a2a_functions:
                        all_startup_code.append("            start_unified_a2a_server(),")
                    all_startup_code.extend(individual_a2a_code)
                    
                    pipeline_agent_startup_code_str = "\n".join(all_startup_code)
                    
                    # Add unified functions for unified server if needed
                    # Note: UNIFIED_A2A_SERVER_TEMPLATE already includes all necessary imports
                    if unified_a2a_functions:
                        unified_functions = "\n".join(unified_a2a_functions) + "\n\n"
                        # Add required imports for unified server
                        unified_imports = """import uvicorn
import logging
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

"""
                    else:
                        unified_functions = ""
                        unified_imports = ""

                    # Build the complete pipeline service content
                    pipeline_service_content = f"""from pathlib import Path
import sys
import asyncio
from topaz_agent_kit.services.base_agent_service import BaseAgentService

# Add agents directory to Python path for imports
sys.path.append(str(Path(__file__).resolve().parents[1] / "agents"))
# Add services directory to Python path for imports (works for both direct execution and module execution)
sys.path.insert(0, str(Path(__file__).resolve().parent))

{unified_imports}{pipeline_agent_imports_str}

{unified_functions}async def start_{pipeline_id}_services():
    \"\"\"Start all {pipeline_id} agent services concurrently\"\"\"
    await asyncio.gather(
{pipeline_agent_startup_code_str}
    )

if __name__ == "__main__":
    # Start all agents
    asyncio.run(start_{pipeline_id}_services())
"""

                    with open(pipeline_service_file, "w", encoding='utf-8') as f:
                        f.write(pipeline_service_content.strip())

                    self.logger.success(
                        f"Generated pipeline service file: {pipeline_service_file}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Failed to generate pipeline service for {pipeline_id}: {e}"
                    )
                    import traceback
                    self.logger.info(f"Traceback for {pipeline_id}: {traceback.format_exc()}")
                    continue

        # Generate global unified service file with ONE unified server per port
        unified_file = services_dir / "unified_service.py"
        
        # Collect ALL agents (pipeline + independent) and group by port
        agents_by_port: dict[int, list[dict]] = {}
        all_service_imports = []
        
        for agent_config in remote_agents:
            agent_id = agent_config.get("id")
            pipeline_id = agent_config.get("_pipeline_id")
            remote = agent_config.get("remote", {})
            url = remote.get("url")
            
            if not url:
                continue
            
            # Generate service name - always use agent_id only (no pipeline prefix)
            # Services are shared across pipelines, so they should be identified by agent_id alone
            service_var_name = f"{agent_id}_service"
            
            service_file_name = f"{agent_id}_service"
            
            # Import individual service
            all_service_imports.append(f"from {service_file_name} import {service_var_name}")
            
            # Parse URL to get port and path
            host, port = self._parse_url_and_port(url)
            path = self._extract_path_from_url(url)
            # Ensure path starts with / if not empty
            if path and not path.startswith('/'):
                path = '/' + path
            elif not path:
                path = f'/{agent_id}'
            
            # Group agents by port
            if port not in agents_by_port:
                agents_by_port[port] = []
            
            agents_by_port[port].append({
                "agent_id": agent_id,
                "service_var_name": service_var_name,
                "path": path
            })
        
        # Generate ONE unified A2A server function per port
        unified_a2a_functions = []
        all_startup_calls = []
        
        for port, agents in agents_by_port.items():
            if not agents:
                continue
            
            app_build_lines = []
            mount_routes = []
            agent_list = [f'"{a["agent_id"]}"' for a in agents]
            first_service = agents[0]["service_var_name"]
            
            for agent in agents:
                app_build_lines.append(
                    f"    {agent['agent_id']}_app = {agent['service_var_name']}.a2a_service.a2a_app.build()"
                )
                # Ensure path ends with /
                mount_path = agent['path'] if agent['path'].endswith('/') else agent['path'] + '/'
                mount_routes.append(
                    f'        Mount("{mount_path}", app={agent["agent_id"]}_app),'
                )
            
            # Generate unified A2A server function for this port
            function_name = f"start_unified_a2a_server_port_{port}"
            unified_a2a_function = self._process_unified_a2a_template(
                UNIFIED_A2A_SERVER_TEMPLATE,
                service_imports="",  # Imports are in unified service content
                app_build_code="\n".join(app_build_lines),
                mount_routes="\n".join(mount_routes),
                pipeline_id=f"port_{port}",
                a2a_port=port,
                agent_list=f"[{', '.join(agent_list)}]",
                first_service_name=first_service,
            )
            
            # Remove duplicate imports from unified template and rename function
            lines = unified_a2a_function.split('\n')
            filtered_lines = []
            in_import_section = True
            for line in lines:
                stripped = line.strip()
                if in_import_section:
                    if (stripped.startswith('from ') or stripped.startswith('import ') or 
                        stripped.startswith('sys.path') or stripped.startswith('# Add ') or
                        stripped == ''):
                        continue
                    else:
                        in_import_section = False
                if not in_import_section:
                    # Rename the function to be port-specific
                    if stripped.startswith('async def start_unified_a2a_server'):
                        filtered_lines.append(f"async def {function_name}():")
                    else:
                        filtered_lines.append(line)
            
            unified_a2a_function_clean = '\n'.join(filtered_lines)
            unified_a2a_functions.append(unified_a2a_function_clean)
            all_startup_calls.append(f"            {function_name}(),")
        
        unified_a2a_function_clean = "\n\n".join(unified_a2a_functions) if unified_a2a_functions else ""
        
        # Build unified service content
        unified_imports = """import uvicorn
import logging
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

"""
        all_service_imports_str = "\n".join(all_service_imports)
        
        # Combine startup code: ONE unified server per port
        all_startup_code_str = "\n".join(all_startup_calls) if all_startup_calls else ""
        
        unified_service_content = f"""from pathlib import Path
import sys
import asyncio

# Add services directory to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

{unified_imports}{all_service_imports_str}

{unified_a2a_function_clean}

async def start_all_agents():
    \"\"\"Start all agent services: ONE unified server per port handling all agents\"\"\"
    await asyncio.gather(
{all_startup_code_str}
    )

if __name__ == "__main__":
    # Start all agents
    asyncio.run(start_all_agents())
"""

        with open(unified_file, "w", encoding='utf-8') as f:
            f.write(unified_service_content.strip())

        self.logger.success(f"Generated unified service file: {unified_file}")

    def get_service_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about service generation.

        Returns:
            Dict containing service generation statistics
        """
        # Future extensibility: Track service generation statistics
        return {
            "total_services_generated": 0,
            "services_by_protocol": {},
            "services_by_agent_type": {},
        }


def main() -> None:
    """CLI entry point for service generation"""
    parser = argparse.ArgumentParser(
        description="Generate service stubs for remote agents from YAML config"
    )
    parser.add_argument(
        "project", help="Path to project root (contains config/pipeline.yml)"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )
    args = parser.parse_args()

    generator = ServiceGenerator()
    exit_code = generator.generate_services(args.project, args.overwrite)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
