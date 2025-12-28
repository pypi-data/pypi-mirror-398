# CRITICAL: Set UTF-8 encoding for Windows compatibility (fixes charmap codec errors)
# This must be done before any other imports that might output Unicode characters
import sys
import os

if sys.platform == "win32":
    # Set environment variable for subprocesses
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Reconfigure stdout/stderr to use UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# CRITICAL: Suppress deprecation warnings BEFORE any imports
# This must be the very first thing in the file to catch warnings emitted during importlib bootstrap
import warnings

# Set default action for DeprecationWarnings to ignore BEFORE any imports
# This catches warnings emitted during importlib bootstrap (e.g., SWIG warnings)
warnings.simplefilter("ignore", DeprecationWarning)

# Now we can safely import other modules
import argparse
import os
from pathlib import Path

# Additional specific suppressions (redundant but explicit for clarity)
# Suppress SWIG-related deprecation warnings (from MCP/C extensions)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPy.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*swigvarlink.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*builtin type.*has no __module__ attribute.*")
# Suppress websockets.legacy deprecation warnings (from uvicorn)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets.legacy")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets.websockets_impl")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.legacy.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*websockets.server.WebSocketServerProtocol.*deprecated.*")
# Suppress sqlite3 datetime adapter deprecation warnings (Python 3.12+)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*datetime adapter.*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlite3")
# Suppress litellm asyncio event loop deprecation warnings (Python 3.12+)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*There is no current event loop.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="litellm.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*asyncio.get_event_loop.*")
# Suppress other library warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.cli.serve_cli import main as serve_cli
from topaz_agent_kit.cli.serve_mcp import main as serve_mcp
from topaz_agent_kit.cli.serve_fastapi import main as serve_fastapi
from topaz_agent_kit.cli.serve_services import main as serve_services
from topaz_agent_kit.cli.project_scaffolder import ProjectScaffolder
from topaz_agent_kit.cli.agent_generator import AgentGenerator
from topaz_agent_kit.cli.service_generator import ServiceGenerator
from topaz_agent_kit.cli.config_validator import ConfigValidator
from topaz_agent_kit.cli.graphviz_generator import GraphvizGenerator

logger = Logger("TopazAgentKitMain")

def discover_available_starters() -> list[str]:
    """Dynamically discover available starter templates from package or project root"""
    try:
        # First try to discover from package (when installed)
        try:
            import importlib.resources
            package_templates = importlib.resources.files("topaz_agent_kit.templates.starters")
            
            available_starters = []
            for item in package_templates.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if it has the required structure (config/pipeline.yml)
                    pipeline_file = item / "config" / "pipeline.yml"
                    if pipeline_file.exists():
                        available_starters.append(item.name)
            
            if available_starters:
                available_starters.sort()
                return available_starters
        except Exception:
            pass
        
        # Fallback to project root directory (for development)
        project_root = Path(__file__).parent.parent.parent.parent
        starters_dir = project_root / "templates" / "starters"
        
        if not starters_dir.exists():
            return ["math_demo", "stock_analysis"]  # Fallback to known starters
        
        # Discover all starter directories
        available_starters = []
        for item in starters_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it has the required structure (config/pipeline.yml)
                pipeline_file = item / "config" / "pipeline.yml"
                if pipeline_file.exists():
                    available_starters.append(item.name)
        
        # Sort for consistent ordering
        available_starters.sort()
        
        # If no starters found, fallback to known ones
        if not available_starters:
            return ["math_demo", "stock_analysis"]
        
        return available_starters
        
    except Exception:
        # Fallback to known starters if discovery fails
        return ["math_demo", "stock_analysis"]

def discover_available_foundations() -> list[str]:
    """Dynamically discover available foundation templates from package or project root"""
    try:
        # First try to discover from package (when installed)
        try:
            import importlib.resources
            package_templates = importlib.resources.files("topaz_agent_kit.templates.foundations")
            
            available_foundations = []
            for item in package_templates.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if it has the required structure (config/pipeline.yml)
                    pipeline_file = item / "config" / "pipeline.yml"
                    if pipeline_file.exists():
                        available_foundations.append(item.name)
            
            if available_foundations:
                available_foundations.sort()
                return available_foundations
        except Exception:
            pass
        
        # Fallback to project root directory (for development)
        project_root = Path(__file__).parent.parent.parent.parent
        foundations_dir = project_root / "templates" / "foundations"
        
        if not foundations_dir.exists():
            return ["basic"]  # Fallback to known foundation
        
        # Discover all foundation directories
        available_foundations = []
        for item in foundations_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it has the required structure (config/pipeline.yml)
                pipeline_file = item / "config" / "pipeline.yml"
                if pipeline_file.exists():
                    available_foundations.append(item.name)
        
        # Sort for consistent ordering
        available_foundations.sort()
        
        # If no foundations found, fallback to known ones
        if not available_foundations:
            return ["basic"]
        
        return available_foundations
        
    except Exception:
        # Fallback to known foundations if discovery fails
        return ["basic"]


def print_rich_help() -> None:
    """Print beautiful Rich-formatted help for Topaz Agent Kit."""
    console = Console()
    
    # Header with logo-like styling
    header = Text("🚀 Topaz Agent Kit", style="bold blue")
    subtitle = Text("Multi-Agent Orchestration Framework", style="italic cyan")
    
    console.print()
    console.print(Panel.fit(
        Columns([header, subtitle], equal=True),
        border_style="blue",
        padding=(0, 1)
    ))
    console.print()
    
    # Key Features
    features_text = Text("✨ Key Features:", style="bold green")
    features = [
        "• Scaffold new projects from templates",
        "• Generate agent code from YAML configurations",
        "• Validate pipeline and UI configurations", 
        "• Serve agents via MCP, FastAPI, or CLI interfaces",
        "• Support for local and remote agent deployment"
    ]
    
    console.print(features_text)
    for feature in features:
        console.print(f"  {feature}", style="white")
    console.print()
    
    # Commands Table with Better Descriptions
    commands_table = Table(
        title="🛠️  Available Commands",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.ROUNDED
    )
    commands_table.add_column("Command", style="cyan", no_wrap=True)
    commands_table.add_column("Description", style="white")
    commands_table.add_column("Long Options", style="yellow", no_wrap=True)
    commands_table.add_column("Short Options", style="green", no_wrap=True)
    
    commands_data = [
        ("init", "Create complete project: scaffold + generate in one command", "--foundation/--starter/--overwrite", "-f/-s/-o"),
        ("scaffold", "Create project structure and files from template (no code generation)", "--foundation/--starter/--overwrite/--no-stubs/--no-remote-services", "-f/-s/-o/-n/-r"),
        ("generate", "Generate Python code from existing pipeline.yml configuration", "--overwrite/--agents/--services/--no-update-impl", "-o/-a/-s/-u"),
        ("validate", "Check pipeline.yml and ui_manifest.yml for errors and consistency", "", ""),
        ("list", "Show available foundation templates and starter projects", "--foundations/--starters/--all", "-f/-s/-a"),
        ("serve", "Run MCP server, FastAPI web interface, or CLI agent interface", "--project/--log-level", "-p/-l")
    ]
    
    for cmd, desc, long_opts, short_opts in commands_data:
        commands_table.add_row(cmd, desc, long_opts, short_opts)
    
    console.print(commands_table)
    console.print()
    
    # Short Options Note
    short_options_text = Text("💡 Short Options Available:", style="bold green")
    console.print(short_options_text)
    console.print("  All long options have short equivalents (e.g., --foundation → -f, --overwrite → -o)")
    console.print("  Use --help with any command to see both long and short options")
    console.print()
    
    # Command Categories
    categories_text = Text("📚 Command Categories:", style="bold green")
    console.print(categories_text)
    
    categories = [
        ("🏗️  Project Creation:", "init, scaffold - Create new agent projects from templates", "blue"),
        ("⚙️  Code Generation:", "generate - Create Python code and configuration", "cyan"),
        ("🔍  Validation:", "validate, list - Check configurations and discover templates", "yellow"),
        ("🚀  Execution:", "serve - Run your agent workflows via various interfaces", "magenta")
    ]
    
    for title, desc, color in categories:
        console.print(f"  {title}", style=color)
        console.print(f"    {desc}", style="white")
        console.print()
    
    # Examples
    examples_text = Text("💡 Quick Examples:", style="bold green")
    console.print(examples_text)
    
    examples = [
        ("Quick start with foundation:", "topaz-agent-kit init --foundation basic ./my_project", "blue"),
        ("Quick start with foundation (short):", "topaz-agent-kit init -f basic ./my_project", "cyan"),
        ("Quick start with starter:", "topaz-agent-kit init --starter math_demo ./my_math_project", "yellow"),
        ("Quick start with starter (short):", "topaz-agent-kit init -s math_demo ./my_math_project", "green"),
        ("Overwrite existing:", "topaz-agent-kit init --starter math_demo ./my_project --overwrite", "magenta"),
        ("Overwrite existing (short):", "topaz-agent-kit init -s math_demo ./my_project -o", "red"),
        ("List foundations:", "topaz-agent-kit list --foundations", "blue"),
        ("List foundations (short):", "topaz-agent-kit list -f", "cyan"),
        ("Start services with custom port:", "topaz-agent-kit serve all --project ./my_project --port 8080", "yellow"),
        ("Start services with custom port (short):", "topaz-agent-kit serve all -u ./my_project -p 8080", "green"),
        ("Generate only agents:", "topaz-agent-kit generate ./my_project --agents", "magenta"),
        ("Generate only agents (short):", "topaz-agent-kit generate ./my_project -a", "red")
    ]
    
    for title, cmd, color in examples:
        console.print(f"  {title}", style="white")
        console.print(f"    {cmd}", style=color)
        console.print()
    
    # Footer
    footer = Text("🌐 For more information, visit: https://github.com/topaz-agent-kit", style="dim")
    console.print(footer)
    console.print()


def print_init_help() -> None:
    """Print beautiful Rich-formatted help for the init command."""
    console = Console()
    
    # Header
    header = Text("🚀 Init Command", style="bold blue")
    subtitle = Text("Quick Start: Create Complete Project in One Command", style="italic cyan")
    
    console.print()
    console.print(Panel.fit(
        Columns([header, subtitle], equal=True),
        border_style="blue",
        padding=(0, 1)
    ))
    console.print()
    
    # Description
    desc_text = Text("The init command is a quick-start command that combines scaffold + generate in one operation.", style="white")
    console.print(desc_text)
    console.print("This creates a fully functional agent workflow project from a starter template with all code and configuration ready to run.")
    console.print()
    
    # Usage
    usage_text = Text("📖 Usage:", style="bold green")
    console.print(usage_text)
    console.print("  topaz-agent-kit init <destination> [--foundation <name> | --starter <name>] [options]")
    console.print()
    console.print("  Note: If no template is specified, defaults to 'basic' foundation", style="dim")
    console.print()
    
    # Arguments Table
    args_table = Table(
        title="🔧 Arguments & Options",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.ROUNDED
    )
    args_table.add_column("Long Option", style="cyan", no_wrap=True)
    args_table.add_column("Short Option", style="yellow", no_wrap=True)
    args_table.add_column("Required", style="red", no_wrap=True)
    args_table.add_column("Description", style="white")
    
    args_data = [
        ("--foundation", "-f", "Optional", "Foundation template (defaults to 'basic' if not specified)"),
        ("--starter", "-s", "Optional", "Starter template (working example)"),
        ("--overwrite", "-o", "No", "Overwrite existing directory"),
        ("destination", "(positional)", "Yes", "Target directory for new project")
    ]
    
    for long_opt, short_opt, required, desc in args_data:
        args_table.add_row(long_opt, short_opt, required, desc)
    
    console.print(args_table)
    console.print()
    
    # Examples
    examples_text = Text("💡 Examples:", style="bold green")
    console.print(examples_text)
    
    examples = [
        ("Quick start (default basic):", "topaz-agent-kit init .", "blue"),
        ("Quick start with foundation:", "topaz-agent-kit init -f basic ./my_project", "cyan"),
        ("Quick start with starter:", "topaz-agent-kit init -s ensemble ./my_math_project", "green"),
        ("Overwrite existing:", "topaz-agent-kit init -s ensemble ./my_project -o", "yellow")
    ]
    
    for title, cmd, color in examples:
        console.print(f"  {title}", style="white")
        console.print(f"    {cmd}", style=color)
        console.print()
    
    # What It Creates
    creates_text = Text("🏗️  What Init Creates:", style="bold green")
    console.print(creates_text)
    
    creates = [
        "• Project directory structure from template",
        "• Configuration files (pipeline.yml, ui_manifest.yml)",
        "• Agent implementation stubs",
        "• Remote service wrappers",
        "• README and documentation files"
    ]
    
    for item in creates:
        console.print(f"  {item}", style="white")
    console.print()
    
    # Available Templates
    templates_text = Text("📋 Available Templates:", style="bold green")
    console.print(templates_text)
    
    foundations = discover_available_foundations()
    starters = discover_available_starters()
    
    console.print("  🏗️  Foundations:", style="cyan")
    for foundation in foundations:
        console.print(f"    • {foundation} - Basic project structure", style="white")
    
    console.print("  🚀 Starters:", style="cyan")
    for starter in starters:
        console.print(f"    • {starter} - Working example with agents", style="white")
    
    console.print()


def print_scaffold_help() -> None:
    """Print beautiful Rich-formatted help for the scaffold command."""
    console = Console()
    
    # Header
    header = Text("🏗️  Scaffold Command", style="bold blue")
    subtitle = Text("Create Project Structure from Template (No Code Generation)", style="italic cyan")
    
    console.print()
    console.print(Panel.fit(
        Columns([header, subtitle], equal=True),
        border_style="blue",
        padding=(0, 1)
    ))
    console.print()
    
    # Description
    desc_text = Text("The scaffold command creates a complete project project structure from a starter template.", style="white")
    console.print(desc_text)
    console.print("This creates the directory structure, configuration files, and basic code templates needed to get started with a specific agent workflow.")
    console.print("Note: This does NOT generate the actual Python code - use 'generate' command for that.")
    console.print()
    
    # Usage
    usage_text = Text("📖 Usage:", style="bold green")
    console.print(usage_text)
    console.print("  topaz-agent-kit scaffold <destination> [--foundation <name> | --starter <name>] [options]")
    console.print()
    
    # Arguments Table
    args_table = Table(
        title="🔧 Arguments & Options",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.ROUNDED
    )
    args_table.add_column("Long Option", style="cyan", no_wrap=True)
    args_table.add_column("Short Option", style="yellow", no_wrap=True)
    args_table.add_column("Required", style="red", no_wrap=True)
    args_table.add_column("Description", style="white")
    
    args_data = [
        ("--foundation", "-f", "One of -f/-s", "Foundation template (basic structure)"),
        ("--starter", "-s", "One of -f/-s", "Starter template (working example)"),
        ("--overwrite", "-o", "No", "Overwrite existing directory"),
        ("--no-stubs", "-n", "No", "Skip generating agent stub files"),
        ("--no-remote-services", "-r", "No", "Skip generating remote service files"),
        ("destination", "(positional)", "Yes", "Target directory for new project")
    ]
    
    for long_opt, short_opt, required, desc in args_data:
        args_table.add_row(long_opt, short_opt, required, desc)
    
    console.print(args_table)
    console.print()
    
    # Examples
    examples_text = Text("💡 Examples:", style="bold green")
    console.print(examples_text)
    
    examples = [
        ("Scaffold basic foundation:", "topaz-agent-kit scaffold . -f basic", "blue"),
        ("Scaffold math demo starter:", "topaz-agent-kit scaffold . -s math_demo", "cyan"),
        ("Scaffold to specific path:", "topaz-agent-kit scaffold ./my_project -s stock_analysis", "yellow"),
        ("Overwrite existing:", "topaz-agent-kit scaffold ./my_project -s math_demo -o", "green"),
        ("Skip stubs and services:", "topaz-agent-kit scaffold . -s basic -n -r", "magenta")
    ]
    
    for title, cmd, color in examples:
        console.print(f"  {title}", style="white")
        console.print(f"    {cmd}", style=color)
        console.print()
    
    # Available Templates
    templates_text = Text("📋 Available Templates:", style="bold green")
    console.print(templates_text)
    
    foundations = discover_available_foundations()
    starters = discover_available_starters()
    
    console.print("  🏗️  Foundations:", style="cyan")
    for foundation in foundations:
        console.print(f"    • {foundation} - Basic project structure", style="white")
    
    console.print("  🚀 Starters:", style="cyan")
    for starter in starters:
        console.print(f"    • {starter} - Working example with agents", style="white")
    
    console.print()


def print_generate_help() -> None:
    """Print beautiful Rich-formatted help for the generate command."""
    console = Console()
    
    # Header
    header = Text("⚙️  Generate Command", style="bold blue")
    subtitle = Text("Generate Python Code from Pipeline Configuration", style="italic cyan")
    
    console.print()
    console.print(Panel.fit(
        Columns([header, subtitle], equal=True),
        border_style="blue",
        padding=(0, 1)
    ))
    console.print()
    
    # Description
    desc_text = Text("The generate command creates Python code from your pipeline.yml configuration.", style="white")
    console.print(desc_text)
    console.print("This generates agent implementations, remote services, and workflow diagrams.")
    console.print("Use this after scaffolding to create the actual working code.")
    console.print()
    
    # Usage
    usage_text = Text("📖 Usage:", style="bold green")
    console.print(usage_text)
    console.print("  topaz-agent-kit generate <project_path> [options]")
    console.print()
    
    # Arguments Table
    args_table = Table(
        title="🔧 Arguments & Options",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.ROUNDED
    )
    args_table.add_column("Long Option", style="cyan", no_wrap=True)
    args_table.add_column("Short Option", style="yellow", no_wrap=True)
    args_table.add_column("Required", style="red", no_wrap=True)
    args_table.add_column("Description", style="white")
    
    args_data = [
        ("project_path", "(positional)", "Yes", "Path to project directory (contains config/pipeline.yml)"),
        ("--overwrite", "-o", "No", "Overwrite existing generated files"),
        ("--agents", "-a", "No", "Generate only agent implementations"),
        ("--services", "-s", "No", "Generate only remote service files"),
        ("--no-update-impl", "-u", "No", "Skip updating existing implementations")
    ]
    
    for long_opt, short_opt, required, desc in args_data:
        args_table.add_row(long_opt, short_opt, required, desc)
    
    console.print(args_table)
    console.print()
    
    # Examples
    examples_text = Text("💡 Examples:", style="bold green")
    console.print(examples_text)
    
    examples = [
        ("Generate everything (default):", "topaz-agent-kit generate ./my_project", "blue"),
        ("Generate only agents:", "topaz-agent-kit generate ./my_project -a", "cyan"),
        ("Generate only services:", "topaz-agent-kit generate ./my_project -s", "yellow"),
        ("Overwrite existing:", "topaz-agent-kit generate ./my_project -o", "magenta"),
        ("Skip implementation updates:", "topaz-agent-kit generate ./my_project -u", "red")
    ]
    
    for title, cmd, color in examples:
        console.print(f"  {title}", style="white")
        console.print(f"    {cmd}", style=color)
        console.print()
    
    # What It Generates
    generates_text = Text("🏗️  What Generate Creates:", style="bold green")
    console.print(generates_text)
    
    generates = [
        "• Agent implementation files from pipeline.yml",
        "• Remote service wrapper classes",
        "• Service registration and configuration",
        "• Import statements and dependencies"
    ]
    
    for item in generates:
        console.print(f"  {item}", style="white")
    console.print()
    
    console.print()




def print_validate_help() -> None:
    """Print beautiful Rich-formatted help for the validate command."""
    console = Console()
    
    # Header
    header = Text("🔍 Validate Command", style="bold blue")
    subtitle = Text("Check Pipeline and UI Configuration Files", style="italic cyan")
    
    console.print()
    console.print(Panel.fit(
        Columns([header, subtitle], equal=True),
        border_style="blue",
        padding=(0, 1)
    ))
    console.print()
    
    # Description
    desc_text = Text("The validate command checks your pipeline.yml and ui_manifest.yml configuration files for errors.", style="white")
    console.print(desc_text)
    console.print("This helps catch configuration issues before running your agents.")
    console.print()
    
    # Usage
    usage_text = Text("📖 Usage:", style="bold green")
    console.print(usage_text)
    console.print("  topaz-agent-kit validate <project_path>")
    console.print()
    
    # Arguments Table
    args_table = Table(
        title="🔧 Arguments",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.ROUNDED
    )
    args_table.add_column("Argument", style="cyan", no_wrap=True)
    args_table.add_column("Required", style="red", no_wrap=True)
    args_table.add_column("Description", style="white")
    
    args_data = [
        ("project_path", "Yes", "Path to project root directory to validate")
    ]
    
    for arg, required, desc in args_data:
        args_table.add_row(arg, required, desc)
    
    console.print(args_table)
    console.print()
    
    # Examples
    examples_text = Text("💡 Examples:", style="bold green")
    console.print(examples_text)
    
    examples = [
        ("Validate configuration in current directory:", "topaz-agent-kit validate .", "blue"),
        ("Validate specific project:", "topaz-agent-kit validate ./my_project")
    ]
    
    for title, cmd, color in examples:
        console.print(f"  {title}", style="white")
        console.print(f"    {cmd}", style=color)
        console.print()
    
    # What It Validates
    validates_text = Text("🔍 What Validate Checks:", style="bold green")
    console.print(validates_text)
    
    validates = [
        "• YAML syntax and structure",
        "• Required agent configurations",
        "• MCP tool availability",
        "• Pipeline workflow consistency",
        "• UI manifest configuration",
        "• File paths and references"
    ]
    
    for item in validates:
        console.print(f"  {item}", style="white")
    console.print()


def print_serve_help() -> None:
    """Print beautiful Rich-formatted help for the serve command."""
    console = Console()
    
    # Header
    header = Text("🚀 Serve Command", style="bold blue")
    subtitle = Text("Start Agent Services (MCP, FastAPI, CLI, Services, or All)", style="italic cyan")
    
    console.print()
    console.print(Panel.fit(
        Columns([header, subtitle], equal=True),
        border_style="blue",
        padding=(0, 1)
    ))
    console.print()
    
    # Description
    desc_text = Text("The serve command starts one or more services to run your agent workflow.", style="white")
    console.print(desc_text)
    console.print("Services can be started individually or all together depending on your needs.")
    console.print()
    
    # Usage
    usage_text = Text("📖 Usage:", style="bold green")
    console.print(usage_text)
    console.print("  topaz-agent-kit serve [service] [options]")
    console.print()
    
    # Arguments Table
    args_table = Table(
        title="🔧 Arguments & Options",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.ROUNDED
    )
    args_table.add_column("Long Option", style="cyan", no_wrap=True)
    args_table.add_column("Short Option", style="yellow", no_wrap=True)
    args_table.add_column("Required", style="red", no_wrap=True)
    args_table.add_column("Description", style="white")
    
    args_data = [
        ("service", "(positional)", "No", "Service to start: mcp, fastapi, cli, services, or all (default: all)"),
        ("--project", "-p", "No", "Path to project root directory (auto-detect if not specified)"),
        ("--log-level", "-l", "No", "Set logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)")
    ]
    
    for long_opt, short_opt, required, desc in args_data:
        args_table.add_row(long_opt, short_opt, required, desc)
    
    console.print(args_table)
    console.print()
    
    # Examples
    examples_text = Text("💡 Examples:", style="bold green")
    console.print(examples_text)
    
    examples = [
        ("Start all services (default):", "topaz-agent-kit serve all -p ./my_project", "blue"),
        ("Start only MCP server:", "topaz-agent-kit serve mcp -p ./my_project", "cyan"),
        ("Start specific MCP server:", "topaz-agent-kit serve mcp -p ./my_project -n solver", "yellow"),
        ("Start only FastAPI service:", "topaz-agent-kit serve fastapi -p ./my_project", "green"),
        ("Start only CLI interface:", "topaz-agent-kit serve cli -p ./my_project", "magenta"),
        ("Start only services:", "topaz-agent-kit serve services -p ./my_project", "green")
    ]
    
    for title, cmd, color in examples:
        console.print(f"  {title}", style="white")
        console.print(f"    {cmd}", style=color)
        console.print()
    
    # Service Details
    services_text = Text("🔧 Service Details:", style="bold green")
    console.print(services_text)
    
    services = [
        ("MCP Server", "Model Context Protocol server for tool access (port from pipeline.yml)", "blue"),
        ("FastAPI", "Web interface and API endpoints (port from pipeline.yml)", "cyan"),
        ("CLI", "Command-line interface for agent interaction (terminal only)", "yellow"),
        ("Services", "Start all agent A2A services via unified_service.py", "yellow")
    ]
    
    for service, desc, color in services:
        console.print(f"  {service}:", style=color)
        console.print(f"    {desc}", style="white")
        console.print()
    
    # Ports
    ports_text = Text("🌐 Ports:", style="bold green")
    console.print(ports_text)
    console.print("  • MCP Server: Configured in pipeline.yml (example: 8050)")
    console.print("  • FastAPI: Configured in pipeline.yml (example: 8090)")
    console.print("  • CLI: No network - terminal only")
    console.print("  • Services: Multiple ports (A2A servers for each agent)")
    console.print()


def print_list_help() -> None:
    """Print beautiful Rich-formatted help for the list command."""
    console = Console()
    
    # Header
    header = Text("📋 List Command", style="bold blue")
    subtitle = Text("Discover Available Templates and Starters", style="italic cyan")
    
    console.print()
    console.print(Panel.fit(
        Columns([header, subtitle], equal=True),
        border_style="blue",
        padding=(0, 1)
    ))
    console.print()
    
    # Description
    desc_text = Text("The list command shows available foundation templates and starter projects.", style="white")
    console.print(desc_text)
    console.print("This helps you discover what's available before creating a new project.")
    console.print()
    
    # Usage
    usage_text = Text("📖 Usage:", style="bold green")
    console.print(usage_text)
    console.print("  topaz-agent-kit list [type] [options]")
    console.print()
    
    # Arguments Table
    args_table = Table(
        title="🔧 Arguments & Options",
        show_header=True,
        header_style="bold magenta",
        border_style="blue",
        box=box.ROUNDED
    )
    args_table.add_column("Long Option", style="cyan", no_wrap=True)
    args_table.add_column("Short Option", style="yellow", no_wrap=True)
    args_table.add_column("Required", style="red", no_wrap=True)
    args_table.add_column("Description", style="white")
    
    args_data = [
        ("--foundations", "-f", "One of -f/-s/-a", "List foundation templates only"),
        ("--starters", "-s", "One of -f/-s/-a", "List starter templates only"),
        ("--all", "-a", "One of -f/-s/-a", "List all templates (foundations + starters)"),
    ]
    
    for long_opt, short_opt, required, desc in args_data:
        args_table.add_row(long_opt, short_opt, required, desc)
    
    console.print(args_table)
    console.print()
    
    # Examples
    examples_text = Text("💡 Examples:", style="bold green")
    console.print(examples_text)
    
    examples = [
        ("List all foundation templates:", "topaz-agent-kit list --foundations", "blue"),
        ("List all foundation templates (short):", "topaz-agent-kit list -f", "cyan"),
        ("List all starter templates:", "topaz-agent-kit list --starters", "yellow"),
        ("List all starter templates (short):", "topaz-agent-kit list -s", "green"),
        ("List everything available:", "topaz-agent-kit list --all", "magenta"),
        ("List everything available (short):", "topaz-agent-kit list -a", "red"),
        ("List using positional argument:", "topaz-agent-kit list foundations", "blue")
    ]
    
    for title, cmd, color in examples:
        console.print(f"  {title}", style="white")
        console.print(f"    {cmd}", style=color)
        console.print()
    
    # Template Types
    types_text = Text("🏗️  Template Types:", style="bold green")
    console.print(types_text)
    
    types = [
        ("Foundations", "Basic project structure and configuration", "cyan"),
        ("Starters", "Working examples with pre-configured agents", "yellow")
    ]
    
    for template_type, desc, color in types:
        console.print(f"  {template_type}:", style=color)
        console.print(f"    {desc}", style="white")
        console.print()


def main() -> None:

    # Enhanced main parser with better description
    parser = argparse.ArgumentParser(
        description="""Topaz Agent Kit - Multi-Agent Orchestration Framework

A powerful toolkit for building, deploying, and orchestrating AI agents using
multiple frameworks (ADK, Agno, CrewAI, LangGraph, OAK, SK) with MCP tools and flexible protocols.

Key Features:
• Scaffold new projects from templates
• Generate agent code from YAML configurations  
• Validate pipeline and UI configurations
• Serve agents via MCP, FastAPI, or CLI interfaces
• Support for local and remote agent deployment

Examples:
  # Quick start: scaffold and generate everything (defaults to basic)
  topaz-agent-kit init .                    # Default basic template
  topaz-agent-kit init -f basic ./my_project  # Explicit basic foundation
  topaz-agent-kit init -s ensemble ./my_project  # Full starter template
  
  # List available templates and starters
  topaz-agent-kit list --foundations
  topaz-agent-kit list -f
  topaz-agent-kit list --starters
  topaz-agent-kit list -s
  
  # Start all services for a project
  topaz-agent-kit serve all --project ./my_math_project
  
  # Generate only agent stubs
  topaz-agent-kit generate ./my_math_project --agents
  
  # Validate configuration
  topaz-agent-kit validate ./my_math_project""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""For more information, visit: https://github.com/topaz-agent-kit
Report issues at: https://github.com/topaz-agent-kit/issues""",
    )
    
    # Note: argparse automatically provides -h/--help, so we don't need to add it manually
    
    sub = parser.add_subparsers(dest="cmd", required=False, title="Commands", 
                               description="Available commands for building and running agent workflows")

    # Enhanced scaffold command
    p_scaffold = sub.add_parser(
        "scaffold",
        help="Create a new project project from a starter template",
        description="Scaffold a complete project project structure from a starter template.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom formatting
    )

    p_scaffold.add_argument("dest", nargs="?", 
                           help="Destination directory for the new project")
    p_scaffold.add_argument("--foundation", "-f", required=False,
                           choices=discover_available_foundations(),
                           help="Foundation template to use (basic, etc.)")
    p_scaffold.add_argument("--starter", "-s", required=False,
                           choices=discover_available_starters(),
                           help="Starter template to use (math_demo, agno_demo, etc.)")
    p_scaffold.add_argument("--overwrite", "-o", action="store_true",
                           help="Overwrite existing directory if it exists")
    p_scaffold.add_argument("--no-stubs", "-n", action="store_true",
                           help="Skip generating agent stub files")
    p_scaffold.add_argument("--no-remote-services", "-r", action="store_true",
                           help="Skip generating remote service files")

    # Enhanced generate command
    p_generate = sub.add_parser(
        "generate",
        help="Generate agent code and services from pipeline configuration",
        description="""Generate agent implementations and remote services
from your pipeline.yml configuration. This creates the actual Python code
that implements your agent workflow.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom formatting
        epilog="""Examples:
  # Generate everything (default)
  topaz-agent-kit generate ./my_project
  
  # Generate only agent implementations
  topaz-agent-kit generate ./my_project --agents
  
  # Generate only remote services
  topaz-agent-kit generate ./my_project --services
  
  # Overwrite existing files
  topaz-agent-kit generate ./my_project --overwrite
""",
    )

    p_generate.add_argument("project", nargs="?",
                           help="Path to project root directory (contains config/pipeline.yml)")
    p_generate.add_argument("--overwrite", "-o", action="store_true",
                           help="Overwrite existing generated files")
    p_generate.add_argument("--agents", "-a", action="store_true",
                           help="Generate only agent implementations")
    p_generate.add_argument("--services", "-s", action="store_true",
                           help="Generate only remote service files")
    p_generate.add_argument("--no-update-impl", "-u", dest="update_impl", action="store_false", default=True,
                           help="Skip updating existing implementations")


    # Enhanced validate command
    p_validate = sub.add_parser(
        "validate",
        help="Validate pipeline and UI configuration files",
        description="""Validate your pipeline.yml and ui_manifest.yml configuration files
for syntax errors, missing required fields, and configuration consistency.
This helps catch configuration issues before running your agents.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom formatting
        epilog="""Examples:
  # Validate configuration in current directory
  topaz-agent-kit validate .
  
  # Validate specific project
  topaz-agent-kit validate ./my_project
  
  # Validate will check:
  # • YAML syntax and structure
  # • Required agent configurations
  # • MCP tool availability
  # • Pipeline workflow consistency""",
    )

    p_validate.add_argument("project", nargs="?",
                           help="Path to project root directory to validate")

    # Enhanced init command
    p_init = sub.add_parser(
        "init",
        help="Quick start: scaffold and generate everything in one command",
        description="""Initialize a complete project project in one command.
This combines scaffold + generate to create a fully functional
        agent workflow project from a starter template.
generated from your pipeline.yml configuration.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom formatting
        epilog="""Examples:
  # Quick start with default basic template (recommended)
  topaz-agent-kit init .
  topaz-agent-kit init ./my_project
  
  # Explicitly use basic foundation (same as default)
  topaz-agent-kit init -f basic ./my_project
  
  # Quick start with starter template (full examples)
  topaz-agent-kit init -s ensemble ./my_project
  topaz-agent-kit init -s math_demo ./math_project
  
  # Overwrite existing directory
  topaz-agent-kit init ./my_project --overwrite
  topaz-agent-kit init -s ensemble ./my_project -o
  
This is equivalent to:
  topaz-agent-kit scaffold ./my_project --starter [template]
  topaz-agent-kit generate ./my_project
  
The generate command automatically creates:
  • Agent implementations from pipeline.yml
  • Remote service wrappers
  • SVG workflow diagrams""",
    )

    p_init.add_argument("dest", nargs="?",
                       help="Destination directory for the new project")
    p_init.add_argument("--foundation", "-f", required=False,
                       choices=discover_available_foundations(),
                       help="Foundation template to use")
    p_init.add_argument("--starter", "-s", required=False,
                       choices=discover_available_starters(),
                       help="Starter template to use (working examples)")
    p_init.add_argument("--overwrite", "-o", action="store_true",
                       help="Overwrite existing directory if it exists")

    # Enhanced list command
    p_list = sub.add_parser(
        "list",
        help="List available templates and starters",
        description="""List available templates and starter projects that can be used
with the init and scaffold commands. This helps you discover what's available
before creating a new project.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom formatting
        epilog="""Examples:
  # List all available foundation templates
  topaz-agent-kit list --foundations
  topaz-agent-kit list -f
  
  # List all available starter templates
  topaz-agent-kit list --starters
  topaz-agent-kit list -s
  
  # List everything available
  topaz-agent-kit list --all
  topaz-agent-kit list -a
  
  # Get help on list command
  topaz-agent-kit list --help""",
    )

    # Add short form flags (these will override the type argument)
    p_list.add_argument("-f", "--foundations", action="store_true",
                       help="List foundation templates")
    p_list.add_argument("-s", "--starters", action="store_true",
                       help="List starter templates")
    p_list.add_argument("-a", "--all", action="store_true",
                       help="List all templates")
    
    # Positional argument (optional when using short flags)
    p_list.add_argument("type", nargs="?", 
                       choices=["foundations", "starters", "all"],
                       help="Type of templates to list (foundations, starters, or all)")

    # Enhanced serve command
    p_serve = sub.add_parser(
        "serve",
        help="Start agent services (MCP server, FastAPI, CLI, Services, or all)",
        description="""Start one or more services to run your agent workflow.
Services can be started individually or all together depending on your needs.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to use custom formatting
        epilog="""Examples:
  # Start all services (default)
  topaz-agent-kit serve all --project ./my_project
  
  # Start only MCP server
  topaz-agent-kit serve mcp --project ./my_project
  
  # Start only FastAPI service
  topaz-agent-kit serve fastapi --project ./my_project
  
  # Start only CLI interface
  topaz-agent-kit serve cli --project ./my_project
  
  # Start only services
  topaz-agent-kit serve services --project ./my_project
  
  # Auto-detect project directory
  topaz-agent-kit serve all
  
Service Details:
  • MCP Server: Model Context Protocol server for tool access (port from pipeline.yml)
  • FastAPI: Web interface and API endpoints (port from pipeline.yml)  
  • CLI: Command-line interface for agent interaction (terminal only)
  • Services: Start all agent A2A services via unified_service.py (multiple ports)
  
Ports: Configured in pipeline.yml (examples: MCP 8050, FastAPI 8090), CLI (no network), Services (multiple ports)""",
    )

    p_serve.add_argument("service", nargs="?",
                        choices=["mcp", "fastapi", "cli", "services", "all"], 
                        help="Service type to run: mcp (Model Context Protocol), fastapi (web interface), cli (command line), services (unified agent services), or all (all services)")
    p_serve.add_argument("--name", "-n",
                        help="Name of specific MCP server to start (default: all servers)")
    p_serve.add_argument("--project", "-p", required=True,
                        help="Path to project root directory")
    p_serve.add_argument("--log-level", "-l",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        default="INFO",
                        help="Set logging level for all services (DEBUG, INFO, WARNING, ERROR). Default: INFO")
    p_serve.add_argument("--ui-dist",
                        help="Serve UI from a local prebuilt directory (overrides embedded UI). Also reads TOPAZ_UI_DIST_DIR")
    p_serve.add_argument("--reload", action="store_true",
                        help="Enable hot reloading for FastAPI backend (development mode)")

    args = parser.parse_args()
    
    # If no command provided, show beautiful Rich help
    if not args.cmd:
        print_rich_help()
        raise SystemExit(0)

    if args.cmd == "scaffold":
        # Check for missing required parameters and show help
        if not args.dest or (not args.foundation and not args.starter):
            print_scaffold_help()
            raise SystemExit(0)
        
        # Call scaffold class
        scaffolder = ProjectScaffolder()
        
        # Determine which template type to use
        if args.foundation and args.starter:
            logger.error("Cannot specify both --foundation and --starter. Choose one.")
            raise SystemExit(1)
        
        dest_path = args.dest
        
        if args.foundation:
            logger.info("Scaffolding foundation '{}' to {}", args.foundation, dest_path)
            scaffolder.scaffold_from_starter(args.foundation, Path(dest_path), overwrite=args.overwrite)
        else:
            logger.info("Scaffolding starter '{}' to {}", args.starter, dest_path)
            scaffolder.scaffold_from_starter(args.starter, Path(dest_path), overwrite=args.overwrite)
        
        raise SystemExit(0)

    if args.cmd == "generate":
        # Check for missing required parameters and show help
        if not args.project:
            print_generate_help()
            raise SystemExit(0)
        
        # Use the generation classes
        
        # Determine what to generate based on flags
        if args.agents and not args.services:
            # Generate only agents
            generator = AgentGenerator()
            exit_code = generator.generate_agents(args.project, args.overwrite)
            raise SystemExit(exit_code)
        elif args.services and not args.agents:
            # Generate only services
            generator = ServiceGenerator()
            exit_code = generator.generate_services(args.project, args.overwrite)
            raise SystemExit(exit_code)
        else:
            # Generate all (default behavior) or combination
            # First generate agents
            generator = AgentGenerator()
            exit_code = generator.generate_agents(args.project, args.overwrite)
            if exit_code != 0:
                raise SystemExit(exit_code)
            
            # Then generate services
            logger.info("Generating services...")
            generator = ServiceGenerator()
            exit_code = generator.generate_services(args.project, args.overwrite)
            if exit_code != 0:
                raise SystemExit(exit_code)
            
            # Finally generate workflow diagrams using Graphviz
            logger.info("Generating workflow diagrams...")
            graphviz_generator = GraphvizGenerator()
            exit_code = graphviz_generator.generate_workflow_diagrams(args.project, args.overwrite)
            raise SystemExit(exit_code)

    if args.cmd == "validate":
        # Check for missing required parameters and show help
        if not args.project:
            print_validate_help()
            raise SystemExit(0)
        
        validator = ConfigValidator()
        exit_code = validator.validate_project(args.project)
        raise SystemExit(exit_code)

    if args.cmd == "list":
        # Check for missing required parameters and show help
        if not args.foundations and not args.starters and not args.all:
            print_list_help()
            raise SystemExit(0)
        
        # Handle short form flags first
        if args.foundations:
            args.type = "foundations"
        elif args.starters:
            args.type = "starters"
        elif args.all:
            args.type = "all"
        
        # List available templates and starters
        if args.type == "starters":
            starters = discover_available_starters()
            logger.info("Available starter templates:")
            for starter in starters:
                logger.info("  • {}", starter)
            logger.info("Use: topaz-agent-kit init -s <name> <destination>")
            
        elif args.type == "foundations":
            foundations = discover_available_foundations()
            logger.info("Available foundation templates:")
            for foundation in foundations:
                logger.info("  • {}", foundation)
            logger.info("Use: topaz-agent-kit init -f <name> <destination>")
            
        elif args.type == "all":
            starters = discover_available_starters()
            foundations = discover_available_foundations()
            
            logger.info("Available foundation templates:")
            for foundation in foundations:
                logger.info("  • {} (foundation)", foundation)
            logger.info("")
            logger.info("Available starter templates:")
            for starter in starters:
                logger.info("  • {} (starter)", starter)
            logger.info("")
            logger.info("Usage:")
            logger.info("  Foundations: topaz-agent-kit init -f <name> <destination>")
            logger.info("  Starters: topaz-agent-kit init -s <name> <destination>")
        
        raise SystemExit(0)

    if args.cmd == "init":
        # Check for missing destination
        if not args.dest:
            print_init_help()
            raise SystemExit(0)
        
        # Determine which template type to use
        if args.foundation and args.starter:
            logger.error("Cannot specify both --foundation and --starter. Choose one.")
            raise SystemExit(1)
        
        dest_path = args.dest
        
        # Default to basic foundation if no template specified
        if not args.foundation and not args.starter:
            logger.info("No template specified, using default 'basic' foundation")
            args.foundation = "basic"
        
        if args.foundation:
            logger.info("Scaffolding foundation '{}' to {}", args.foundation, dest_path)
            template_name = args.foundation
        elif args.starter:
            logger.info("Scaffolding starter '{}' to {}", args.starter, dest_path)
            template_name = args.starter
        else:
            # This should never happen due to validation above, but just in case
            logger.error("No template type specified")
            raise SystemExit(1)
        
        # Call scaffold class
        scaffolder = ProjectScaffolder()
        scaffolder.scaffold_from_starter(template_name, Path(dest_path), overwrite=args.overwrite)
        
        # Then generate agents and services
        project_dir = str(Path(dest_path).resolve())
        logger.info("Generating agents and services for {}", project_dir)
        
        # Use the generation classes
        
        # Generate agents
        generator = AgentGenerator()
        exit_code = generator.generate_agents(project_dir, True)  # Always overwrite after scaffold
        if exit_code != 0:
            raise SystemExit(exit_code)
        
        # Generate services
        logger.info("Generating services...")
        generator = ServiceGenerator()
        exit_code = generator.generate_services(project_dir, True)  # Always overwrite after scaffold
        if exit_code != 0:
            raise SystemExit(exit_code)
        
        # Generate workflow diagrams
        logger.info("Generating workflow diagrams...")
        svg_generator = GraphvizGenerator()
        exit_code = svg_generator.generate_workflow_diagrams(project_dir, True)  # Always overwrite after scaffold
        if exit_code != 0:
            raise SystemExit(exit_code)
        
        # Validate the generated configuration
        logger.info("Validating generated configuration...")
        try:
            from topaz_agent_kit.core.configuration_engine import ConfigurationEngine
            config_engine = ConfigurationEngine(Path(project_dir))
            config_result = config_engine.load_and_validate()
            
            if not config_result.is_valid:
                logger.error("Configuration validation failed:")
                for error in config_result.errors:
                    logger.error("  • {}", error)
                raise SystemExit(1)
            
            logger.success("Configuration validation passed successfully!")
            
        except Exception as e:
            logger.error("Configuration validation failed: {}", e)
            raise SystemExit(1)
        
        logger.success("Project initialization completed successfully!")
        logger.info("Your project is ready to use. Next steps:")
        logger.info("  • Start services: topaz-agent-kit serve all --project {}", project_dir)
        logger.info("  • Validate config: topaz-agent-kit validate {}", project_dir)
        raise SystemExit(0)

    if args.cmd == "serve":
        # Check for missing required parameters and show help
        if not hasattr(args, 'service') or not args.service:
            print_serve_help()
            raise SystemExit(0)
        
        if not args.project:
            # Try to auto-detect, but if it fails, show help
            try:
                project_dir = Path.cwd()
                while project_dir != project_dir.parent:
                    if (project_dir / "config" / "pipeline.yml").exists():
                        break
                    project_dir = project_dir.parent
                else:
                    print_serve_help()
                    raise SystemExit(0)
            except Exception:
                print_serve_help()
                raise SystemExit(0)
        
        # Apply log level if specified
        if args.log_level:
            try:
                Logger.set_global_level_from_string(args.log_level)
                logger.info("Log level set to: {}", args.log_level)
            except Exception as e:
                logger.warning("Failed to set log level to {}: {}", args.log_level, e)
        
        # Determine project directory
        if args.project:
            project_dir = Path(args.project).resolve()
        else:
            # Auto-detect: start from current directory and look for pipeline.yml
            project_dir = Path.cwd()
            while project_dir != project_dir.parent:
                if (project_dir / "config" / "pipeline.yml").exists():
                    break
                project_dir = project_dir.parent
            else:
                logger.error("No project directory found (no pipeline.yml in parent directories)")
                raise SystemExit(1)
        
        logger.info("Starting services for project: {}", project_dir)
        
        if args.service in ["mcp", "all"]:
            logger.info("Starting MCP server...")
            
            # Change to project directory
            os.chdir(project_dir)
            
            # Start MCP server using the base service directly
            try:
                logger.info("MCP server initialized, starting server...")
                serve_mcp(str(project_dir), args.name, args.log_level)
                
            except Exception as e:
                logger.error("Failed to start MCP server: {}", e)
                raise SystemExit(1)
        
        if args.service in ["fastapi", "all"]:
            logger.info("Starting FastAPI service...")
            
            # Change to project directory
            os.chdir(project_dir)
            
            # Start FastAPI service using the existing main function
            try:
                logger.info("FastAPI service initialized, starting server...")
                serve_fastapi(str(project_dir), args.log_level, args.ui_dist, args.reload)
                
            except Exception as e:
                logger.error("Failed to start FastAPI service: {}", e)
                raise SystemExit(1)
        
        if args.service in ["cli", "all"]:
            logger.info("Starting CLI application")
            
            # CLI is a terminal application, no network setup needed
            # Just change to project directory and start interactive session
            try:
                logger.info("CLI application initialized, starting interactive session...")
                serve_cli(str(project_dir))
                
            except Exception as e:
                logger.error("Failed to start CLI application: {}", e)
                raise SystemExit(1)
        
        if args.service in ["services", "all"]:
            logger.info("Starting services...")
            
            # Change to project directory
            os.chdir(project_dir)
            
            try:
                logger.info("Services initialized, starting unified service...")
                serve_services(str(project_dir), args.log_level)
                
            except Exception as e:
                logger.error("Failed to start services: {}", e)
                raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover
    main()

