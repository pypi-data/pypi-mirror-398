"""Tool loader for pipeline-specific local tools.

Loads tools from project directories, normalizes names, and filters
based on agent configuration patterns.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import importlib
import sys
import os
import fnmatch

from topaz_agent_kit.local_tools.registry import ToolSpec, get_registered_tools, clear_registry
from topaz_agent_kit.utils.mcp_utils import matches_tool_patterns
from topaz_agent_kit.utils.logger import Logger


class LocalToolLoader:
    """Loads and filters pipeline-specific local tools."""
    
    def __init__(self, project_dir: Path, logger: Optional[Logger] = None):
        """Initialize loader.
        
        Args:
            project_dir: Path to project root directory
            logger: Logger instance (creates one if not provided)
        """
        self.project_dir = Path(project_dir)
        self.logger = logger or Logger("LocalToolLoader")
    
    def load_for_agent(
        self,
        agent_config: Dict[str, Any],
        pipeline_id: Optional[str] = None
    ) -> List[ToolSpec]:
        """Load tools for an agent based on its local_tools configuration.
        
        Args:
            agent_config: Agent configuration dict (must contain local_tools section)
            pipeline_id: Optional pipeline ID (if not provided, derived from module paths)
        
        Returns:
            List of ToolSpec objects that match the agent's allowlist patterns
        
        Raises:
            ValueError: If local_tools config is invalid
            ImportError: If tool modules cannot be imported
        """
        local_tools_config = agent_config.get("local_tools")
        if not local_tools_config:
            return []
        
        # Validate required fields
        modules = local_tools_config.get("modules", [])
        if not modules:
            raise ValueError("local_tools.modules is required and cannot be empty")
        
        tools_patterns = local_tools_config.get("tools", [])
        if not tools_patterns:
            raise ValueError("local_tools.tools is required and cannot be empty")
        
        toolkits = local_tools_config.get("toolkits", [])
        
        # Add project_dir to Python path so tools modules can be imported
        # Use os.path.normpath and os.path.abspath for OS-agnostic path handling
        project_dir_resolved = self.project_dir.resolve()
        project_dir_str = os.path.normpath(os.path.abspath(str(project_dir_resolved)))
        
        # Normalize sys.path entries for comparison (OS-agnostic)
        normalized_sys_path = [os.path.normpath(os.path.abspath(p)) for p in sys.path]
        
        path_added = False
        if project_dir_str not in normalized_sys_path:
            sys.path.insert(0, project_dir_str)
            path_added = True
            self.logger.debug("Added project directory to Python path: {}", project_dir_str)
        
        try:
            # Import modules and collect registered tools
            all_specs = []
            for module_path in modules:
                try:
                    # Import the module
                    self.logger.debug("Importing tool module: {}", module_path)
                    module = importlib.import_module(module_path)
                    
                    # Ensure Optional is available in module namespace for MAF/Pydantic
                    # This fixes Pydantic v2 forward reference errors when MAF creates models
                    # from function signatures with Optional types
                    from typing import Optional
                    if not hasattr(module, 'Optional'):
                        setattr(module, 'Optional', Optional)
                    # Also ensure typing module is available
                    if not hasattr(module, 'typing'):
                        import typing
                        setattr(module, 'typing', typing)
                    
                    # Get tools registered by this module
                    module_tools = get_registered_tools(module_path)
                    
                    # Derive pipeline_id from module path if not provided
                    # Expected format: tools.<pipeline_id>.<module_name>
                    if not pipeline_id and module_path.startswith("tools."):
                        parts = module_path.split(".")
                        if len(parts) >= 2:
                            pipeline_id = parts[1]
                    
                    # Set pipeline_id on all tools from this module
                    for spec in module_tools:
                        spec.pipeline_id = pipeline_id
                        all_specs.append(spec)
                    
                    self.logger.debug("Found {} tools in module {}", len(module_tools), module_path)
                    
                except ImportError as e:
                    self.logger.error("Failed to import tool module {}: {}", module_path, e)
                    raise
                except Exception as e:
                    self.logger.error("Error loading tools from module {}: {}", module_path, e)
                    raise
        finally:
            # Remove project_dir from sys.path if we added it
            # Use normalized comparison for OS-agnostic removal
            if path_added:
                # Find and remove the path (may be in different format due to OS differences)
                normalized_sys_path = [os.path.normpath(os.path.abspath(p)) for p in sys.path]
                if project_dir_str in normalized_sys_path:
                    # Find the actual entry in sys.path (may have different format)
                    for i, path_entry in enumerate(sys.path):
                        normalized_entry = os.path.normpath(os.path.abspath(path_entry))
                        if normalized_entry == project_dir_str:
                            sys.path.pop(i)
                            self.logger.debug("Removed project directory from Python path: {}", project_dir_str)
                            break
        
        # Log tools before filtering (use simple names)
        if all_specs:
            self.logger.info("Local tools count before filtering: {}", len(all_specs))
            tool_names_before = [spec.name for spec in all_specs]
            for name in sorted(tool_names_before):
                self.logger.info("  - {}", name)
        
        # Normalize patterns (convert dots to underscores for matching)
        normalized_patterns = [p.replace(".", "_") for p in tools_patterns]
        self.logger.debug("Normalized patterns: {}", normalized_patterns)
        self.logger.debug("Toolkit filter: {}", toolkits)
        
        # Filter tools by patterns
        filtered_specs = []
        for spec in all_specs:
            # Use simple tool name for matching (no prefixes)
            tool_name = spec.name
            
            # Check toolkit match first (if toolkit filter is provided)
            toolkit_match = True
            if toolkits:
                toolkit_match = spec.toolkit in toolkits
            
            # Check pattern match against simple tool name
            # Patterns can be:
            # 1. Exact tool name: "rate_case_validate_and_summarize"
            # 2. Toolkit wildcard: "rate_case.*" (matches all tools in rate_case toolkit)
            # 3. Toolkit.tool_name: "spider_dataset.get_database_path" (matches specific tool in toolkit)
            # 4. Wildcard: "rate_case_*" (matches tools starting with rate_case_)
            pattern_match = False
            
            # Try matching tool name directly
            pattern_match = matches_tool_patterns(tool_name, normalized_patterns, None)
            
            # Try toolkit-based matching for dotted patterns
            if not pattern_match:
                for orig_pattern in tools_patterns:
                    if "." in orig_pattern:
                        parts = orig_pattern.split(".", 1)
                        pattern_toolkit = parts[0]
                        pattern_tool_part = parts[1] if len(parts) > 1 else None
                        
                        # Check if toolkit matches
                        if pattern_toolkit == spec.toolkit:
                            if pattern_tool_part:
                                # Pattern like "toolkit.tool_name" or "toolkit.*"
                                if "*" in pattern_tool_part:
                                    # Wildcard pattern like "toolkit.*" - match any tool in toolkit
                                    pattern_match = True
                                    break
                                else:
                                    # Exact pattern like "toolkit.tool_name" - match specific tool
                                    # Normalize the tool part (dots to underscores) and match
                                    normalized_tool_part = pattern_tool_part.replace(".", "_")
                                    if fnmatch.fnmatchcase(tool_name, normalized_tool_part):
                                        pattern_match = True
                                        break
                            else:
                                # Pattern is just "toolkit." - match any tool in toolkit
                                pattern_match = True
                                break
            
            if pattern_match and toolkit_match:
                filtered_specs.append(spec)
                self.logger.debug("Tool {} matches patterns (toolkit: {})", tool_name, spec.toolkit)
            else:
                self.logger.debug("Tool {} does not match (toolkit: {}, pattern_match: {}, toolkit_match: {})", 
                                 tool_name, spec.toolkit, pattern_match, toolkit_match)
        
        # Log tools after filtering (use simple names)
        if filtered_specs:
            self.logger.success("Local tools count after filtering: {}", len(filtered_specs))
            tool_names_after = [spec.name for spec in filtered_specs]
            for name in sorted(tool_names_after):
                self.logger.success("  - {}", name)
        else:
            self.logger.warning("No local tools matched patterns ({} tools before filtering)", len(all_specs))
        
        self.logger.info(
            "Loaded {} tools ({} after filtering) from {} modules",
            len(all_specs),
            len(filtered_specs),
            len(modules)
        )
        
        return filtered_specs
    
    def _normalize_pattern(self, pattern: str) -> str:
        """Normalize a tool name pattern to canonical underscore form.
        
        Converts: pipeline.toolkit.tool -> pipeline__toolkit__tool
        
        Args:
            pattern: Tool name pattern (may contain dots or underscores)
        
        Returns:
            Normalized pattern with double underscores
        """
        # Replace dots with double underscores
        return pattern.replace(".", "__")
    
    @staticmethod
    def normalize_tool_name(name: str) -> str:
        """Normalize a tool name to canonical underscore form.
        
        Args:
            name: Tool name (may be dotted or underscore)
        
        Returns:
            Normalized name with double underscores
        """
        return name.replace(".", "__")

