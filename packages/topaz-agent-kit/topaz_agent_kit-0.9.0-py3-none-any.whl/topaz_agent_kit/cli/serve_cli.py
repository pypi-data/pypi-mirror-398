import argparse
import asyncio
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from topaz_agent_kit.core.configuration_engine import ConfigurationEngine
from topaz_agent_kit.core.ag_ui_event_emitter import AGUIEventEmitter
from topaz_agent_kit.utils.helper import helper
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.orchestration.assistant import Assistant, AssistantResponse
from topaz_agent_kit.orchestration.orchestrator import Orchestrator
import traceback

logger = Logger("InteractiveCLI")

def parse_user_input(user_input: str) -> tuple[list[str], list[str], str]:
    """Parse user input for upload flags and extract message, handling spaces in file paths with single or double quotes."""
    # Find all -s and -r flag occurrences
    session_files = []
    rag_files = []
    
    # Process -s flags (session files)
    s_matches = list(re.finditer(r"-s\s+", user_input))
    for match in s_matches:
        start_pos = match.end()
        # Extract files after this -s flag until next flag or end
        remaining = user_input[start_pos:]
        next_flag_pos = len(remaining)
        
        # Find next flag position
        next_s = re.search(r"-s\s+", remaining)
        next_r = re.search(r"-r\s+", remaining)
        
        if next_s:
            next_flag_pos = min(next_flag_pos, next_s.start())
        if next_r:
            next_flag_pos = min(next_flag_pos, next_r.start())
        
        # Extract file list from this segment
        file_segment = remaining[:next_flag_pos].strip()
        if file_segment:
            # Parse files from this segment (handle quoted and unquoted)
            files = []
            current_file = ""
            in_quotes = False
            quote_char = None
            
            for char in file_segment:
                if char in ['"', "'"] and not in_quotes:
                    in_quotes = True
                    quote_char = char
                    # Don't include the opening quote
                elif char == quote_char and in_quotes:
                    in_quotes = False
                    quote_char = None
                    # Don't include the closing quote
                elif char == ' ' and not in_quotes:
                    if current_file.strip():
                        files.append(current_file.strip())
                        current_file = ""
                else:
                    current_file += char
            
            if current_file.strip():
                files.append(current_file.strip())
            
            session_files.extend(files)
    
    # Process -r flags (RAG files) - same logic as -s
    r_matches = list(re.finditer(r"-r\s+", user_input))
    for match in r_matches:
        start_pos = match.end()
        remaining = user_input[start_pos:]
        next_flag_pos = len(remaining)
        
        next_s = re.search(r"-s\s+", remaining)
        next_r = re.search(r"-r\s+", remaining)
        
        if next_s:
            next_flag_pos = min(next_flag_pos, next_s.start())
        if next_r:
            next_flag_pos = min(next_flag_pos, next_r.start())
        
        file_segment = remaining[:next_flag_pos].strip()
        if file_segment:
            files = []
            current_file = ""
            in_quotes = False
            quote_char = None
            
            for char in file_segment:
                if char in ['"', "'"] and not in_quotes:
                    in_quotes = True
                    quote_char = char
                    # Don't include the opening quote
                elif char == quote_char and in_quotes:
                    in_quotes = False
                    quote_char = None
                    # Don't include the closing quote
                elif char == ' ' and not in_quotes:
                    if current_file.strip():
                        files.append(current_file.strip())
                        current_file = ""
                else:
                    current_file += char
            
            if current_file.strip():
                files.append(current_file.strip())
            
            rag_files.extend(files)
    
    # Error if both used together
    if session_files and rag_files:
        raise ValueError("Cannot use both -s and -r flags together")
    
    # Error if flags are used without files
    if re.search(r"-s\s*$", user_input) or re.search(r"-r\s*$", user_input):
        raise ValueError("Upload flags (-s or -r) must be followed by file paths")
    
    # Clean message (remove all flag sections)
    clean_message = user_input
    for match in reversed(list(re.finditer(r"-[sr]\s+", user_input))):
        # Find the end of this flag section
        start_pos = match.start()
        remaining = user_input[match.end():]
        next_flag_pos = len(remaining)
        
        # Find next flag position
        next_s = re.search(r"-s\s+", remaining)
        next_r = re.search(r"-r\s+", remaining)
        
        if next_s:
            next_flag_pos = min(next_flag_pos, next_s.start())
        if next_r:
            next_flag_pos = min(next_flag_pos, next_r.start())
        
        # Remove this entire flag section
        end_pos = match.end() + next_flag_pos
        clean_message = clean_message[:start_pos] + clean_message[end_pos:]
    
    clean_message = clean_message.strip()
    
    # Error if flags are used without message
    if (session_files or rag_files) and not clean_message:
        raise ValueError("Message required when using upload flags (-s or -r)")
    
    return session_files, rag_files, clean_message


async def start_interactive_cli(project_dir: str) -> None:
    """Start the interactive CLI for the specified project."""
    
    logger.info("Starting interactive CLI for project: {}", project_dir)
    
    # FIXED: Use new ConfigurationEngine instead of old PipelineLoader
    try:
        project_path = Path(project_dir)
        config_engine = ConfigurationEngine(project_path)
        config_result = config_engine.load_and_validate()
        
        if not config_result.is_valid:
            error_msgs = config_result.errors if config_result.errors else ["Configuration validation failed"]
            logger.error("Configuration validation failed: {}", error_msgs)
            raise RuntimeError(f"Configuration validation failed: {error_msgs}")
        
        cfg = config_result.pipeline_config
        logger.debug("Configuration loaded successfully using new ConfigurationEngine")
        
    except Exception as e:
        logger.error("Failed to load configuration: {}", e)
        raise
    
    def render_event(evt: dict) -> None:
        try:
            etype = evt.get("type") or evt.get("phase") or "event"
            agent = (evt.get("agent") or evt.get("role") or "").upper()
            logger.debug("CLI received event: type={}, agent={}, keys={}", etype, agent, list(evt.keys()))
            if etype == "tool_call":
                tool = evt.get("tool_id") or evt.get("tool") or "tool"
                args_s = evt.get("args")
                logger.debug("[TOOL] {}: {} {}", agent, tool, json.dumps(args_s, ensure_ascii=False))
            elif etype == "prompt":
                prompt = evt.get("prompt") or evt.get("text") or ""
                logger.debug("[PROMPT] {}: {}{}", agent, prompt[:200], '…' if len(prompt) > 200 else '')
            elif etype == "agent_start":
                logger.debug("--- {} START ---", agent)
            elif etype == "agent_end":
                logger.debug("--- {} END ---", agent)
            elif etype == "log":
                level = evt.get("level", "INFO")
                msg = evt.get("message") or evt.get("summary") or ""
                logger.debug("[{}] {}: {}", level, agent, msg)
            elif etype in ["text_message_start", "TEXT_MESSAGE_START"]:
                logger.debug("--- {} OUTPUT START ---", agent)
            elif etype in ["text_message_content", "TEXT_MESSAGE_CONTENT"]:
                content = evt.get("content") or evt.get("text") or evt.get("delta") or ""
                logger.debug("{}", content)
            elif etype in ["text_message_end", "TEXT_MESSAGE_END"]:
                logger.debug("--- {} OUTPUT END ---", agent)
        except Exception:
            pass

    # Create emitter at module level with event capture
    captured_events = []
    
    def emit_and_capture(evt: dict) -> None:
        # Capture the event for pipeline_events
        captured_events.append(evt)
        # Also render for CLI display
        render_event(evt if isinstance(evt, dict) else {})
    
    emitter = AGUIEventEmitter(emit_and_capture)
    emitter._captured_events = captured_events

    # Interactive session picker
    selected_session_id: Optional[str] = None
    try:
        # Initialize Orchestrator to access database
        temp_orch = Orchestrator(cfg, project_dir)
        
        # Get all active sessions
        sessions = temp_orch.get_all_sessions(status="active")
        
        if sessions:
            print("\n📋 Available Sessions:")
            print("  [0] New session")
            
            # Sort by last_accessed (most recent first)
            sorted_sessions = sorted(sessions, key=lambda s: s.last_accessed if hasattr(s, 'last_accessed') else datetime.min, reverse=True)
            
            # Get turn counts for each session
            for idx, session in enumerate(sorted_sessions[:10], start=1):  # Show max 10 recent sessions
                session_id = session.id
                title = getattr(session, 'title', 'New chat') or 'New chat'
                
                # Get turn count
                turns = temp_orch.get_turns_for_session(session_id)
                turn_count = len(turns) if turns else 0
                
                # Format last accessed time
                if hasattr(session, 'last_accessed') and session.last_accessed:
                    time_ago = datetime.now() - session.last_accessed
                    if time_ago.total_seconds() < 3600:
                        time_str = f"{int(time_ago.total_seconds() / 60)} min ago"
                    elif time_ago.total_seconds() < 86400:
                        time_str = f"{int(time_ago.total_seconds() / 3600)} hour ago" if time_ago.total_seconds() < 7200 else f"{int(time_ago.total_seconds() / 3600)} hours ago"
                    else:
                        time_str = f"{int(time_ago.total_seconds() / 86400)} day ago" if time_ago.total_seconds() < 172800 else f"{int(time_ago.total_seconds() / 86400)} days ago"
                else:
                    time_str = "unknown"
                
                print(f"  [{idx}] {title} ({turn_count} turns, {time_str})")
            
            # Get user selection
            while True:
                try:
                    choice = input("\nSelect session (0-{}): ".format(len(sorted_sessions) if len(sorted_sessions) < 10 else 10)).strip()
                    choice_num = int(choice)
                    
                    if choice_num == 0:
                        # Create new session
                        selected_session_id = None
                        break
                    elif 1 <= choice_num <= len(sorted_sessions) and choice_num <= 10:
                        # Restore selected session
                        selected_session = sorted_sessions[choice_num - 1]
                        selected_session_id = selected_session.id
                        logger.info("Restoring session: {} ({})", selected_session_id, getattr(selected_session, 'title', 'New chat'))
                        break
                    else:
                        print("Invalid selection. Please enter a number between 0 and {}.".format(len(sorted_sessions) if len(sorted_sessions) < 10 else 10))
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    print("\n\nExiting...")
                    return
        else:
            # No existing sessions, create new
            logger.info("No existing sessions found, creating new session")
            selected_session_id = None
    except Exception as e:
        # If database access fails, continue with new session
        logger.warning("Could not access session database: {}. Creating new session.", e)
        selected_session_id = None

    # Use Assistant as primary entry point
    try:
        logger.debug("Using Assistant as primary entry point")
        assistant = Assistant(cfg, project_dir=project_dir, emitter=emitter, session_id=selected_session_id)
        await assistant.initialize()
        logger.debug("Assistant created successfully")
    except Exception as e:
        logger.error("Failed to initialize Assistant: {}", e)
        raise
    
    logger.debug("Assistant initialized successfully")
    if selected_session_id:
        logger.info("Session restored: {}", selected_session_id)
    else:
        logger.info("New session created: {}", assistant._session_id)

    async def run_once(text: str) -> None:
        logger.info("Running turn...")
        # Clear captured events for this turn
        captured_events.clear()

        try:
            logger.debug("Calling assistant.execute_assistant_agent with text: {}", text)
            out = await assistant.execute_assistant_agent(text, {})
            logger.debug("Assistant returned: {} (type: {})", out, type(out))
            
            logger.success("Turn completed, result: {} chars", len(str(out)) if out else 0)
            if out:
                # Assistant returns AssistantResponse Pydantic model
                if isinstance(out, AssistantResponse):
                    logger.success(f"Assistant Response: {out.assistant_response}")
                    if out.error:
                        logger.error(f"Error: {out.error}")
                elif isinstance(out, dict):
                    # Fallback for backward compatibility
                    logger.success(f"Assistant Response: {out.get('assistant_response')}")
                    if out.get('error'):
                        logger.error(f"Error: {out.get('error')}")
                else:
                    logger.success(f"Assistant Response: {str(out)}")
            else:
                logger.error("No result returned from assistant")
                logger.debug("Full assistant output: {}", out)
        except Exception as e:
            logger.error("Error during turn execution: {}", e)
            logger.error("Traceback: {}", traceback.format_exc())

    # Start interactive chat loop
    logger.info("Interactive chat started. Type 'quit' or 'q' to leave.")
    
    # Use asyncio to handle the interactive loop
    loop = asyncio.get_event_loop()

    async def cleanup() -> None:
        logger.info("Shutting down CLI service...")
        try:
            await assistant.cleanup()
            logger.success("Assistant cleanup completed")
        except Exception as e:
            logger.warning("Assistant cleanup failed: {}", e)
    
    while True:
        try:
            # Get user input (this is blocking, but that's okay for CLI)
            user = input("You (Type 'quit' or 'q' to leave) > ").strip()
        except (EOFError, KeyboardInterrupt):
            logger.info("")
            await cleanup()
            break
        if not user:
            continue
        if user.lower() in ("quit", "q"):  # noqa: WPS331
            await cleanup()
            break
        
        # Parse for file uploads
        session_files, rag_files, clean_message = parse_user_input(user)
        
        if session_files:
            # Session upload: validate message is provided
            if not clean_message.strip():
                logger.error("Message required for session uploads (-s)")
                continue
            
            # Check for duplicate files within the same turn
            unique_files = []
            seen_files = set()
            for file_path in session_files:
                if file_path in seen_files:
                    logger.warning("Skipping duplicate file in same turn: {}", file_path)
                    continue
                seen_files.add(file_path)
                unique_files.append(file_path)
            
            if not unique_files:
                logger.error("No unique files to upload")
                continue
            
            # Upload files to session storage
            uploaded_paths = []
            for file_path in unique_files:
                try:
                    # Store file in session storage
                    from topaz_agent_kit.core.file_storage import FileStorageService
                    file_storage = FileStorageService(
                        rag_files_path=config_result.rag_files_path,
                        user_files_path=config_result.user_files_path
                    )
                    
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    file_ext = Path(file_path).suffix.lower().lstrip('.') if Path(file_path).suffix else 'unknown'
                    storage_result = file_storage.store_file(
                        file_content=file_content,
                        filename=Path(file_path).name,
                        file_type=file_ext,
                        storage_type="session",
                        session_id=assistant._session_id
                    )
                    
                    uploaded_paths.append(storage_result['path'])
                    logger.info("File uploaded to session: {} -> {}", file_path, storage_result['path'])
                    
                except Exception as e:
                    logger.error("Failed to upload file {}: {}", file_path, e)
                    continue
            
            if uploaded_paths:
                # Execute with session files
                result = await assistant.execute_assistant_agent(
                    user_input=clean_message,
                    file_paths=uploaded_paths,
                    original_filenames=[Path(f).name for f in uploaded_paths],
                    upload_intent="session"
                )
                logger.success("Session upload completed")
                logger.output("Result: {}", result)
            else:
                logger.error("No files were successfully uploaded")
                
        elif rag_files:
            # RAG upload: process with full ingestion
            logger.info("RAG upload detected, processing files...")
            
            # Check for duplicate files within the same turn
            unique_files = []
            seen_files = set()
            for file_path in rag_files:
                if file_path in seen_files:
                    logger.warning("Skipping duplicate file in same turn: {}", file_path)
                    continue
                seen_files.add(file_path)
                unique_files.append(file_path)
            
            if not unique_files:
                logger.error("No unique files to upload")
                continue
            
            # Execute with RAG files
            result = await assistant.execute_assistant_agent(
                user_input=clean_message,
                file_paths=unique_files,
                original_filenames=[Path(f).name for f in unique_files],
                upload_intent="rag"
            )
            
            logger.success("RAG processing completed")
            logger.output("Result: {}", result)
        else:
            # Regular message - go through assistant
            await run_once(clean_message)
    

def main(project_dir: str | None = None) -> None:
    """Start CLI service - either standalone or from main.py."""
    logger = Logger("CLIService")
    logger.info("Starting CLI service")
    
    if project_dir is None:
        # Standalone mode - parse arguments and start CLI
        parser = argparse.ArgumentParser(
            description="CLI chat to run agent pipeline turns",
            epilog="Examples:\n"
                   "  %(prog)s --text 'what is 5 + 3?'          # Single turn\n"
                   "  %(prog)s --text '-s file.pdf Process this' # Session upload\n"
                   "  %(prog)s --text '-r file.pdf'              # RAG upload\n"
                   "  %(prog)s --log-level DEBUG                 # Debug mode\n"
                   "  %(prog)s --project-dir ./math_demo       # Custom directory"
        )
        parser.add_argument("--text", dest="text", default=None, help="Single-turn text. If omitted, starts interactive chat")
        parser.add_argument("--project-dir", dest="project_dir", default=None, help="Override auto-detected project directory")
        parser.add_argument("--log-level", dest="log_level", default=None, 
                          choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                          help="Set logging level (DEBUG, INFO, WARNING, ERROR)")
        args = parser.parse_args()

        # Apply log level if specified
        if args.log_level:
            try:
                Logger.set_global_level_from_string(args.log_level)
                logger.info("Log level set to: {}", args.log_level)
            except Exception as e:
                logger.warning("Failed to set log level to {}: {}", args.log_level, e)
        
        # Use helper to find project directory if not provided
        if args.project_dir:
            project_dir = args.project_dir
            logger.info("Using provided project directory: {}", project_dir)
        else:
            # Auto-detect using helper
            project_dir = str(helper.find_project_dir(Path.cwd()))
            logger.info("Auto-detected project directory: {}", project_dir)

        # Handle single-turn mode
        if args.text is not None:
            # Single turn mode
            logger.info("Running single turn with text: {}", args.text)
            asyncio.run(start_interactive_cli(project_dir))
            return
        
        # Interactive mode
        asyncio.run(start_interactive_cli(project_dir))
    else:
        # Called from main.py - start interactive CLI directly
        asyncio.run(start_interactive_cli(project_dir))


if __name__ == "__main__":  # pragma: no cover
    main()

