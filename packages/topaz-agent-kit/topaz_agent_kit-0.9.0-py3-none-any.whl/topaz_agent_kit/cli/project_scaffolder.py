import argparse
import sys
import os
import time
from pathlib import Path
from typing import Dict  # noqa: F401
import textwrap
import shutil

# # Suppress NLTK SSL warnings that come from dependencies
# warnings.filterwarnings("ignore", message=".*SSL: CERTIFICATE_VERIFY_FAILED.*")
# warnings.filterwarnings("ignore", message=".*Error loading.*nltk_data.*")
# warnings.filterwarnings("ignore", message=".*nltk_data.*")

# # Set environment variable to suppress NLTK downloads
# os.environ.setdefault("NLTK_DATA", "/tmp/nltk_data")
# os.environ.setdefault("NLTK_DOWNLOAD", "false")

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.cli.agent_generator import AgentGenerator
from topaz_agent_kit.cli.service_generator import ServiceGenerator


PIPELINE_YML = """name: "{title}"
description: "Generated pipeline from starter template"

nodes:
{nodes_block}

pattern:
  type: sequential
  steps:
{pattern_steps}
"""


class ProjectScaffolder:
    """
    Scaffolds new projects from starter templates.
    Provides extensible framework for creating new agent workflows.
    """

    def __init__(self):
        self.logger = Logger("ProjectScaffolder")

    def _indent(self, n: int, s: str) -> str:
        """Helper method to indent text by n spaces."""
        return " " * n + s

    def _slugify(self, name: str) -> str:
        """Convert name to URL-safe slug."""
        s = (name or "").strip().lower().replace(" ", "_")
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
        return "".join(ch for ch in s if ch in allowed) or "agent"

    def _copy_gmail_credentials(self, target_dir: Path) -> None:
        """Copy Gmail credentials (client_secret.json, credentials.json, gmail_token.json) to target project.
        
        Looks for credentials in multiple locations (in order):
        1. Current working directory (where user runs the command)
        2. Development project root (when running from source)
        3. Target project's parent directory
        
        Copies all found credential files (doesn't stop after first one).
        """
        try:
            import os
            from pathlib import Path
            
            # List of credential files to copy (in order of preference, but copy all found)
            credential_files = ["client_secret.json", "credentials.json", "gmail_token.json"]
            
            # Strategy 1: Check current working directory (where user runs the command)
            # This works for both installed package and development mode
            cwd = Path.cwd()
            
            # Strategy 2: Check development project root (fallback for dev mode)
            # Go up from src/topaz_agent_kit/cli/project_scaffolder.py -> src/topaz_agent_kit/cli/ -> src/topaz_agent_kit/ -> src/ -> project_root/
            dev_project_root = Path(__file__).parent.parent.parent.parent
            
            # Strategy 3: Check target project's parent directory
            target_parent = target_dir.parent
            
            # Try all locations
            search_locations = [
                ("current working directory", cwd),
                ("development project root", dev_project_root),
                ("target project parent", target_parent),
            ]
            
            copied_count = 0
            found_files = set()  # Track which files we've already copied to avoid duplicates
            
            for location_name, search_dir in search_locations:
                for cred_file in credential_files:
                    if cred_file in found_files:
                        continue  # Already copied this file
                    
                    source_file = search_dir / cred_file
                    if source_file.exists() and source_file.is_file():
                        target_file = target_dir / cred_file
                        if not target_file.exists() or self._should_overwrite(target_file):
                            shutil.copy2(source_file, target_file)
                            self.logger.success(
                                "Copied Gmail credentials ({}) from {} to project directory",
                                cred_file,
                                location_name
                            )
                            copied_count += 1
                            found_files.add(cred_file)
            
            if copied_count == 0:
                # No credentials found - this is optional, so just log debug
                self.logger.debug("Gmail credentials not found - email toolkit will search other locations")
            
        except Exception as e:
            self.logger.warning("Failed to copy Gmail credentials: {}", e)
    
    def _should_overwrite(self, file_path: Path) -> bool:
        """Check if file should be overwritten (always True for now, can be made configurable)."""
        return True

    def _write_files(
        self,
        root: Path,
        cfg: dict,
        *,
        overwrite: bool = False,
        generate_stubs: bool = False,
        generate_remote_services: bool = False,
    ) -> None:
        """Write scaffold files to the target directory."""
        # Only create the configuration scaffold; code will be generated via `generate`
        (root / "config").mkdir(parents=True, exist_ok=True)

        # .env
        if overwrite or not (root / ".env").exists():
            (root / ".env").write_text(
                textwrap.dedent(
                    """
            # Azure OpenAI Configuration
            AZURE_OPENAI_API_BASE=
            AZURE_OPENAI_API_KEY=
            AZURE_OPENAI_DEPLOYMENT=
            AZURE_OPENAI_MODEL=
            AZURE_OPENAI_API_VERSION=
            
            # Google AI Configuration
            GOOGLE_API_KEY=
            
            # Anthropic Configuration
            ANTHROPIC_API_KEY=
            
            # OpenAI Configuration
            OPENAI_API_KEY=
            
            # Ollama Configuration (if used)
            OLLAMA_BASE_URL=http://localhost:11434            

            # DeepSeek Configuration (for MCP model selection)
            DEEPSEEK_API_KEY=

            # Temperature and Max Tokens Configuration
            TEMPERATURE=
            MAX_TOKENS=

            # OpenRouter Configuration (for MCP model selection)
            OPENROUTER_API_KEY=

            # Tavily Configuration (for MCP web search tools)
            TAVILY_API_KEY=

            # Browserless Configuration (for MCP browser tools)
            BROWSERLESS_API_KEY=

            # SSL Configuration
            SSL_CERT_FILE=
            GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=
            """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

        pipeline_path = root / "config" / "pipeline.yml"
        if overwrite or not pipeline_path.exists():
            # Generate pattern-only pipeline.yml (MVP-6.0)
            nodes_block = ""
            pattern_steps = ""

            for a in cfg.get("agents", []):
                aid = a.get("id") or "agent"
                config_file = f"agents/{aid}.yml"

                # Add node definition
                nodes_block += self._indent(2, f"- id: {aid}\n")
                nodes_block += self._indent(4, f"config_file: {config_file}\n")

                # Add pattern step
                pattern_steps += self._indent(4, f"- node: {aid}\n")

            pipeline = PIPELINE_YML.format(
                title=cfg.get("title", "My Demo"),
                nodes_block=nodes_block,
                pattern_steps=pattern_steps,
            )
            pipeline_path.write_text(pipeline, encoding="utf-8")

        # Minimal pyproject.toml so users can `uv sync` per-project deps
        pyproject_path = root / "pyproject.toml"
        if overwrite or not pyproject_path.exists():
            project_pkg = root.name.replace("-", "_")
            pyproject_path.write_text(
                textwrap.dedent(
                    f"""# Generated by topaz-agent-kit scaffold
[project]
name = "{project_pkg}"
version = "0.1.0"
description = "Topaz Agent Kit project"
requires-python = ">=3.9"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["*"]
exclude = ["tests*", "test*"]
"""
                ),
                encoding="utf-8",
            )

        # README.md
        readme_path = root / "README.md"
        if overwrite or not readme_path.exists():
            readme_path.write_text(
                textwrap.dedent(
                    f"""# {cfg.get("title", "My Demo")}

This project was scaffolded by [Topaz Agent Kit](https://github.com/your-org/topaz-agent-kit).

## Setup

1. Install dependencies: `uv sync`
2. Configure your environment variables in `.env`
3. Run: `uv run python cli_app.py`

## Configuration

- `config/pipeline.yml` - Agent workflow definition
- `config/ui_manifest.yml` - UI configuration
- `.env` - Environment variables

## Development

- `agents/` - Agent implementations
- `services/` - Service wrappers
- `ui/` - Frontend assets
"""
                ),
                encoding="utf-8",
            )

        # Generate stubs if requested
        if generate_stubs:
            try:
                generator = AgentGenerator()
                result = generator.generate_agents(root, overwrite=overwrite)
                if result == 0:
                    self.logger.info("Generated agent stubs")
                else:
                    self.logger.warning("Agent stub generation failed")
            except Exception as e:
                self.logger.warning("Failed to generate agent stubs: {}", e)

        # Generate remote services if requested
        if generate_remote_services:
            try:
                generator = ServiceGenerator()
                result = generator.generate_services(root, overwrite=overwrite)
                if result == 0:
                    self.logger.info("Generated remote service stubs")
                else:
                    self.logger.warning("Remote service stub generation failed")
            except Exception as e:
                self.logger.warning("Failed to generate remote service stubs: {}", e)

    def scaffold_from_starter(
        self, starter_name: str, target_dir: Path, *, overwrite: bool = False
    ) -> None:
        """Scaffold a project from a starter template or template."""
        try:
            template_path = None
            template_type = None

            # First try to locate template from package (when installed)
            try:
                import importlib.resources

                # Try starters first
                package_templates = importlib.resources.files(
                    "topaz_agent_kit.templates.starters"
                )
                template_path = package_templates / starter_name
                if template_path.exists():
                    template_type = "starter"
                    self.logger.info(
                        "Found starter template in package: {}", template_path
                    )
                else:
                    # Try foundations
                    package_templates = importlib.resources.files(
                        "topaz_agent_kit.templates.foundations"
                    )
                    template_path = package_templates / starter_name
                    if template_path.exists():
                        template_type = "foundation"
                        self.logger.info(
                            "Found foundation template in package: {}", template_path
                        )
                    else:
                        template_path = None
            except Exception:
                template_path = None

            # Fallback: Try local development templates
            if not template_path:
                try:
                    # Get project root (3 levels up: cli/project_scaffolder.py -> cli/ -> topaz_agent_kit/ -> src/ -> project_root)
                    project_root = Path(__file__).parent.parent.parent.parent

                    # Try starters first
                    local_templates = (
                        project_root
                        / "src"
                        / "topaz_agent_kit"
                        / "templates"
                        / "starters"
                        / starter_name
                    )
                    if local_templates.exists():
                        template_path = local_templates
                        template_type = "starter"
                        self.logger.info(
                            "Found starter template in development: {}", template_path
                        )
                    else:
                        # Try foundations
                        local_templates = (
                            project_root
                            / "src"
                            / "topaz_agent_kit"
                            / "templates"
                            / "foundations"
                            / starter_name
                        )
                        if local_templates.exists():
                            template_path = local_templates
                            template_type = "foundation"
                            self.logger.info(
                                "Found foundation template in development: {}",
                                template_path,
                            )
                except Exception as e:
                    self.logger.warning("Failed to check local templates: {}", e)

            # Template not found anywhere
            if not template_path:
                self.logger.error(
                    "Template '{}' not found in package or development environment",
                    starter_name,
                )
                return

            self.logger.info(
                "Scaffolding from {} '{}' to {}",
                template_type,
                starter_name,
                target_dir,
            )

            # 1) Copy template files
            if (template_path / "config").exists():
                shutil.copytree(
                    template_path / "config", target_dir / "config", dirs_exist_ok=True
                )

            # Copy prompts to config/prompts/ (new structure)
            if (template_path / "prompts").exists():
                prompts_dst = target_dir / "config" / "prompts"
                prompts_dst.mkdir(parents=True, exist_ok=True)
                shutil.copytree(
                    template_path / "prompts", prompts_dst, dirs_exist_ok=True
                )
                self.logger.info("Copied prompts to config/prompts/")

            # Copy schemas to config/schemas/ (new structure)
            if (template_path / "schemas").exists():
                schemas_dst = target_dir / "config" / "schemas"
                schemas_dst.mkdir(parents=True, exist_ok=True)
                shutil.copytree(
                    template_path / "schemas", schemas_dst, dirs_exist_ok=True
                )
                self.logger.info("Copied schemas to config/schemas/")
            if (template_path / "data").exists():
                shutil.copytree(
                    template_path / "data", target_dir / "data", dirs_exist_ok=True
                )
            if (template_path / "services").exists():
                shutil.copytree(
                    template_path / "services",
                    target_dir / "services",
                    dirs_exist_ok=True,
                )
            if (template_path / "agents").exists():
                shutil.copytree(
                    template_path / "agents", target_dir / "agents", dirs_exist_ok=True
                )
            if (template_path / "utils").exists():
                shutil.copytree(
                    template_path / "utils", target_dir / "utils", dirs_exist_ok=True
                )
            if (template_path / "tools").exists():
                shutil.copytree(
                    template_path / "tools", target_dir / "tools", dirs_exist_ok=True
                )
                self.logger.info("Copied tools from template to: {}", target_dir / "tools")
            
            # Copy requisites from template if it exists
            if (template_path / "requisites").exists():
                shutil.copytree(
                    template_path / "requisites", target_dir / "requisites", dirs_exist_ok=True
                )
                self.logger.info("Copied requisites from template to: {}", target_dir / "requisites")

            # Copy scripts from template if it exists
            if (template_path / "scripts").exists():
                scripts_dst = target_dir / "scripts"
                scripts_dst.mkdir(parents=True, exist_ok=True)
                shutil.copytree(
                    template_path / "scripts", scripts_dst, dirs_exist_ok=True
                )
                self.logger.info("Copied scripts from template to: {}", scripts_dst)

            # Copy README if it exists
            if (template_path / "README.md").exists():
                shutil.copy2(template_path / "README.md", target_dir / "README.md")

            # Copy .env.example if it exists in template
            env_example_src = template_path / ".env.example"
            if env_example_src.exists():
                shutil.copy2(env_example_src, target_dir / ".env.example")
                self.logger.success("Copied .env.example from template to: {}", target_dir / ".env.example")

            # 2) Copy only ui_manifest.yml and ui/static/assets/ (no more UI code copying)
            # Copy ui_manifest.yml from template config
            ui_manifest_src = template_path / "config" / "ui_manifest.yml"
            ui_manifest_dst = target_dir / "config" / "ui_manifest.yml"
            self.logger.info("Checking for ui_manifest.yml at: {}", ui_manifest_src)
            if ui_manifest_src.exists():
                shutil.copy2(ui_manifest_src, ui_manifest_dst)
                self.logger.success(
                    "Copied ui_manifest.yml from template to: {}", ui_manifest_dst
                )
            else:
                self.logger.warning(
                    "No ui_manifest.yml found in template at: {}", ui_manifest_src
                )

            # Copy entire UI directory structure if provided: templates/<name>/ui/
            template_ui = template_path / "ui"
            self.logger.info("Checking for template UI structure at: {}", template_ui)
            if template_ui.exists():
                self.logger.info(
                    "Found template UI structure, copying from: {}", template_ui
                )
                ui_dst = target_dir / "ui"
                ui_dst.mkdir(parents=True, exist_ok=True)

                # Copy entire UI directory structure recursively
                shutil.copytree(template_ui, ui_dst, dirs_exist_ok=True)
                self.logger.success(
                    "Copied entire UI directory structure: {} -> {}",
                    template_ui,
                    ui_dst,
                )
            else:
                self.logger.warning(
                    "No template UI structure found at: {}", template_ui
                )

            # 3) Copy service wrapper files into project (from base kit services)
            # try:
            #     current_file = Path(__file__).resolve()
            #     base_services_dir = current_file.parents[2] / "topaz_agent_kit" / "services"

            #     # Copy service wrapper files
            #     service_files = [
            #         ("cli_app.py", target_dir / "cli_app.py"),  # Now using base kit cli_app via serve cli
            #         ("flask_app.py", target_dir / "flask_app.py"),
            #         ("fastapi_service.py", target_dir / "services" / "fastapi_service.py"),  # Now using base service directly
            #         ("mcp_service.py", target_dir / "services" / "mcp_service.py"),  # Now using base service directly
            #         ("gateway.py", target_dir / "services" / "gateway.py"),
            #     ]

            #     for src_name, dst_path in service_files:
            #         try:
            #             src_path = base_services_dir / src_name
            #             if src_path.is_file():
            #                 dst_path.parent.mkdir(parents=True, exist_ok=True)
            #                 dst_path.write_bytes(src_path.read_bytes())
            #         except Exception as e:
            #             self.logger.warning("Failed to copy {}: {}", src_name, e)
            # except Exception as e:
            #     self.logger.warning("Failed to copy service wrappers: {}", e)

            # 4) Copy .env, .gitignore, and scripts from package (not from template)
            try:
                # Get package directory
                import topaz_agent_kit

                package_dir = Path(topaz_agent_kit.__file__).parent

                # Copy .env from package
                package_env = package_dir / ".env"
                if package_env.exists():
                    shutil.copy2(package_env, target_dir / ".env")
                    self.logger.success("Copied .env from package")
                else:
                    self.logger.debug("No .env found in package")

                # Copy .gitignore from package
                package_gitignore = package_dir / ".gitignore"
                if package_gitignore.exists():
                    shutil.copy2(package_gitignore, target_dir / ".gitignore")
                    self.logger.success("Copied .gitignore from package")
                else:
                    self.logger.debug("No .gitignore found in package")

                # Copy scripts from package (scripts are now in src/topaz_agent_kit/scripts/)
                # This works for both development mode (package_dir points to src/topaz_agent_kit/)
                # and installed package mode (package_dir points to installed package location)
                scripts_src = package_dir / "scripts"
                scripts_dst = target_dir / "scripts"
                
                if scripts_src.exists() and scripts_src.is_dir():
                    # Safety check: make sure source is not the same as destination
                    if scripts_src.resolve() == scripts_dst.resolve():
                        self.logger.debug("Scripts source and destination are the same, skipping: {}", scripts_src)
                    else:
                        # Remove destination if it exists (ensure complete removal for clean overwrite)
                        if scripts_dst.exists():
                            self.logger.debug("Removing existing scripts directory: {}", scripts_dst)
                            shutil.rmtree(scripts_dst, ignore_errors=True)
                            # Verify removal completed (wait a moment if needed, especially on Windows)
                            max_retries = 10
                            for i in range(max_retries):
                                if not scripts_dst.exists():
                                    break
                                time.sleep(0.1)
                            if scripts_dst.exists():
                                self.logger.warning("Scripts directory still exists after removal attempt, forcing removal")
                                try:
                                    shutil.rmtree(scripts_dst, ignore_errors=False)
                                except Exception as e:
                                    self.logger.error("Failed to remove scripts directory: {}", e)
                                    # Try to remove individual files and directories as fallback (bottom-up)
                                    try:
                                        # Remove all files first
                                        for root, dirs, files in os.walk(scripts_dst, topdown=False):
                                            for file in files:
                                                try:
                                                    file_path = os.path.join(root, file)
                                                    os.chmod(file_path, 0o777)  # Make writable on Windows
                                                    os.remove(file_path)
                                                except Exception:
                                                    pass
                                            # Remove directories (bottom-up)
                                            for dir_name in dirs:
                                                try:
                                                    dir_path = os.path.join(root, dir_name)
                                                    os.chmod(dir_path, 0o777)  # Make writable on Windows
                                                    os.rmdir(dir_path)
                                                except Exception:
                                                    pass
                                        # Finally remove root directory
                                        os.rmdir(scripts_dst)
                                    except Exception as e2:
                                        self.logger.error("Fallback removal also failed: {}", e2)
                                        # Last resort: try one more time with shutil
                                        shutil.rmtree(scripts_dst, ignore_errors=True)
                        
                        # Ensure parent directory exists
                        scripts_dst.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy the entire scripts directory (fresh copy, overwrites everything)
                        self.logger.debug("Copying scripts from {} to {}", scripts_src, scripts_dst)
                        try:
                            shutil.copytree(scripts_src, scripts_dst, dirs_exist_ok=False)
                        except FileExistsError:
                            # If directory still exists (shouldn't happen after removal, but handle it)
                            self.logger.warning("Scripts directory still exists, doing file-by-file copy to ensure overwrite")
                            # Do file-by-file copy to ensure all files are overwritten
                            scripts_dst.mkdir(parents=True, exist_ok=True)
                            for root, dirs, files in os.walk(scripts_src):
                                # Calculate relative path from source
                                rel_path = os.path.relpath(root, scripts_src)
                                if rel_path == '.':
                                    dst_dir = scripts_dst
                                else:
                                    dst_dir = scripts_dst / rel_path
                                dst_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Copy all files, overwriting existing ones
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    dst_file = dst_dir / file
                                    shutil.copy2(src_file, dst_file)
                                    self.logger.debug("Copied file: {} -> {}", src_file, dst_file)
                        self.logger.success("Copied scripts to: {}", scripts_dst)
                else:
                    self.logger.debug("Scripts folder not found in project root or package")

                # Copy docs/workflows from workspace root (for local dev) or package (for installed package)
                # Try package first (for installed package)
                package_docs_workflows = package_dir / "docs" / "workflows"
                # Try workspace root (for local dev) - 3 levels up from this file
                project_root = Path(__file__).parent.parent.parent.parent
                workspace_docs_workflows = project_root / "docs" / "workflows"
                
                docs_workflows_dst = target_dir / "docs" / "workflows"
                
                # Determine source: prefer package if it exists, otherwise use workspace root
                docs_workflows_src = None
                source_location = None
                
                if package_docs_workflows.exists() and package_docs_workflows.is_dir():
                    docs_workflows_src = package_docs_workflows
                    source_location = "package"
                elif workspace_docs_workflows.exists() and workspace_docs_workflows.is_dir():
                    docs_workflows_src = workspace_docs_workflows
                    source_location = "workspace root"
                
                if docs_workflows_src:
                    docs_workflows_dst.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(
                        docs_workflows_src, docs_workflows_dst, dirs_exist_ok=True
                    )
                    self.logger.success("Copied docs/workflows from {} to: {}", source_location, docs_workflows_dst)
                else:
                    self.logger.debug("docs/workflows folder not found in package or workspace root")

            except Exception as e:
                self.logger.warning(
                    "Failed to copy .env/.gitignore/scripts/docs from package: {}", e
                )

            # 5) Copy Gmail credentials if they exist in project root
            self._copy_gmail_credentials(target_dir)

            self.logger.success(
                "Scaffolded from starter '{}' to {}", starter_name, target_dir
            )
            return
        except Exception as e:
            self.logger.error(
                "Failed to scaffold from starter '{}': {}", starter_name, e
            )

    def scaffold_project(
        self,
        target_dir: Path,
        *,
        overwrite: bool = False,
        generate_stubs: bool = True,
        generate_remote_services: bool = True,
    ) -> None:
        """Scaffold a basic project with default configuration."""
        cfg = {"title": "My Demo", "agents": []}
        self._write_files(
            target_dir,
            cfg,
            overwrite=overwrite,
            generate_stubs=generate_stubs,
            generate_remote_services=generate_remote_services,
        )

        # Copy Gmail credentials if they exist in project root
        self._copy_gmail_credentials(target_dir)

        self.logger.info("Created project at {}", target_dir)


def main() -> None:
    """CLI entry point for scaffolding."""
    parser = argparse.ArgumentParser(description="Scaffold a new project")
    parser.add_argument("target", help="Target directory for the new project")
    parser.add_argument("--starter", help="Starter template to use")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument(
        "--no-stubs", action="store_true", help="Skip agent stub generation"
    )
    parser.add_argument(
        "--no-remote-services",
        action="store_true",
        help="Skip remote service generation",
    )
    args = parser.parse_args()

    target_dir = Path(args.target)
    if target_dir.exists() and not args.overwrite:
        print(
            f"Target directory {target_dir} already exists. Use --overwrite to overwrite."
        )
        sys.exit(1)

    scaffolder = ProjectScaffolder()

    if args.starter:
        # Scaffold from starter template
        scaffolder.scaffold_from_starter(
            args.starter, target_dir, overwrite=args.overwrite
        )
    else:
        # Scaffold basic project
        gen_stubs = not args.no_stubs
        gen_remote = not args.no_remote_services
        scaffolder.scaffold_project(
            target_dir,
            overwrite=args.overwrite,
            generate_stubs=gen_stubs,
            generate_remote_services=gen_remote,
        )


if __name__ == "__main__":  # pragma: no cover
    main()
