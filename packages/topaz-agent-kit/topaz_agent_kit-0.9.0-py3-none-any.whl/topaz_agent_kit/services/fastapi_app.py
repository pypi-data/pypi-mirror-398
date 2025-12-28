import asyncio
import json
import os
import traceback
import subprocess
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path
import importlib
from datetime import datetime
import time

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response
from starlette.staticfiles import StaticFiles
import logging

from topaz_agent_kit.utils.file_upload import FileUploadError
from topaz_agent_kit.core.ag_ui_event_emitter import AGUIEventEmitter
from topaz_agent_kit.core.pipeline_loader import PipelineLoader
from topaz_agent_kit.orchestration import Orchestrator
from topaz_agent_kit.utils.logger import Logger, remove_opentelemetry_console_handlers
from topaz_agent_kit.services.ag_ui_service import AGUIService
from topaz_agent_kit.utils.pdf_highlighter import PDFHighlighter
from topaz_agent_kit.orchestration.assistant import Assistant, AssistantResponse
from topaz_agent_kit.core.file_storage import FileStorageService
from chromadb import PersistentClient
from topaz_agent_kit.core.database_manager import DatabaseManager
from topaz_agent_kit.core.chat_storage import ChatStorage
from topaz_agent_kit.core.session_manager import SessionManager
from topaz_agent_kit.utils.path_resolver import find_repository_root


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for graceful startup and shutdown"""
    logger = Logger("FastAPIApp")
    # Startup
    logger.info("FastAPI application starting up")
    yield
    # Shutdown
    logger.info("FastAPI application shutting down gracefully")
    # Give time for active connections to close
    await asyncio.sleep(0.1)


def create_app(project_dir: str, ui_dist_dir: str | None = None) -> FastAPI:
    logger = Logger("FastAPIApp")
    logger.info("Creating FastAPI application for project: {}", project_dir)
    
    cfg, ui_manifest = PipelineLoader(project_dir).load()
    logger.debug("Configuration loaded successfully")

    app = FastAPI(title="Topaz Agent Kit API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.debug("CORS middleware added")
    
    # Add proxy headers middleware for reverse proxy support (external access)
    # This allows the app to work behind proxies/load balancers
    @app.middleware("http")
    async def proxy_headers_middleware(request: Request, call_next):
        """Handle proxy headers for external access"""
        # Forward common proxy headers to help with external access
        # This is useful when behind reverse proxies, load balancers, or NAT
        forwarded_host = request.headers.get("X-Forwarded-Host")
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        forwarded_for = request.headers.get("X-Forwarded-For")
        
        # Log proxy headers for debugging (only in debug mode)
        if logger.isEnabledFor(logging.DEBUG) and (forwarded_host or forwarded_proto or forwarded_for):
            logger.debug("Proxy headers detected - Host: {}, Proto: {}, For: {}", 
                        forwarded_host, forwarded_proto, forwarded_for)
        
        response = await call_next(request)
        return response

    # Add cache-busting middleware for JavaScript files and favicons
    @app.middleware("http")
    async def cache_bust_middleware(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path.lower()
        # Cache-bust JavaScript files and icon/favicon files
        if path.endswith('.js') or 'favicon' in path or 'icon' in path or path.endswith('.ico') or path.endswith('.png'):
            # Only apply to icon-related files (not all PNGs)
            if 'favicon' in path or 'icon' in path or path.endswith('.ico') or '/assets/topaz-logo.png' in path:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            elif path.endswith('.js'):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        return response

    orchestrator = Orchestrator(cfg, project_dir=project_dir)
    logger.debug("Orchestrator created successfully")
    
    # Create PDF highlighter instance
    pdf_highlighter = PDFHighlighter()
    logger.debug("PDF highlighter created successfully")
    
    # Initialize shared services once (instead of per-request)
    file_storage = None
    chroma_client = None
    chat_storage = None
    session_manager = None
    db_manager = None
    
    def get_shared_services():
        nonlocal file_storage, chroma_client, chat_storage, session_manager, db_manager
        
        if file_storage is None:
            # Get file paths from orchestrator config
            rag_files_path = orchestrator.validated_config.rag_files_path if orchestrator.validated_config else "./data/rag_files"
            user_files_path = orchestrator.validated_config.user_files_path if orchestrator.validated_config else "./data/user_files"
            
            if not Path(rag_files_path).is_absolute():
                rag_files_path = str(Path(project_dir) / rag_files_path)
            if not Path(user_files_path).is_absolute():
                user_files_path = str(Path(project_dir) / user_files_path)
                
            file_storage = FileStorageService(rag_files_path, user_files_path)
            
            # Get ChromaDB path from orchestrator config
            chromadb_path = orchestrator.validated_config.chromadb_path if orchestrator.validated_config else "./data/chroma_db"
            if not Path(chromadb_path).is_absolute():
                chromadb_path = str(Path(project_dir) / chromadb_path)
            
            # Get chat.db path
            chatdb_path = orchestrator.validated_config.chatdb_path if orchestrator.validated_config else "./data/chat.db"
            if not Path(chatdb_path).is_absolute():
                chatdb_path = str(Path(project_dir) / chatdb_path)
            
            # Initialize ChromaDB client
            chroma_client = PersistentClient(path=chromadb_path)
            
            # Initialize chat database
            chat_storage = ChatStorage(chatdb_path)
            session_manager = SessionManager(chat_storage)
            db_manager = DatabaseManager(chat_storage, session_manager)
            
            logger.info("Shared services initialized once")
        
        return file_storage, chroma_client, chat_storage, session_manager, db_manager
    
    history: list[dict] = []
    log_buffer: list[str] = []
    activity: list[dict] = []  # bounded buffer of recent activity events

    sessions: dict[int, list[dict]] = {}
    current_session_id: int | None = None
    # AG-UI adapter session queues (session_id -> asyncio.Queue[str])
    agui_session_queues: dict[int, asyncio.Queue[str]] = {}
    # HITL approval waiters: session_id -> { gate_id -> Future }
    hitl_waiters: dict[int, dict[str, asyncio.Future]] = {}
    # AG-UI service instances per session (session_id -> AGUIService)
    agui_services: dict[int, AGUIService] = {}
    # Run counters per session (session_id -> counter)
    session_run_counters: dict[int, int] = {}
    # AG-UI emitters per session (session_id -> AGUIEventEmitter)
    agui_emitters: dict[int, AGUIEventEmitter] = {}
    # Assistant 
    agui_assistants: dict[int, Assistant] = {}
    initialized_assistants: set[int] = set()


    def _fresh_waiter_future(session_id: int, gate_id: str) -> asyncio.Future:
        futs = hitl_waiters.setdefault(session_id, {})
        old = futs.get(gate_id)
        try:
            if old and not old.done():
                old.cancel()
        except Exception:
            pass
        fut = asyncio.get_event_loop().create_future()
        futs[gate_id] = fut
        return fut

    # Setup logging mirror handler for UI logs (mirror FastAPI/uvicorn and app logs)
    class _UIBufferHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
            try:
                ts = getattr(record, "asctime", None)
                if not ts:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                level = record.levelname
                name = record.name
                msg = self.format(record)
                # Avoid double timestamp in msg if formatter adds it
                # Keep only message after the last ' - ' if present (uvicorn style)
                if " - " in msg:
                    msg = msg.split(" - ", 2)[-1]
                line = f"{ts} | {level} | {name} | {msg}"
                log_buffer.append(line)
                if len(log_buffer) > 1000:
                    del log_buffer[: len(log_buffer) - 1000]
            except Exception:
                pass

    # UI logging handler - respect global log level instead of forcing DEBUG
    ui_handler = _UIBufferHandler()
    # Don't force DEBUG level - let Topaz Logger control it
    ui_handler.setLevel(logging.getLogger().getEffectiveLevel())
    # Formatter consistent with root logger
    ui_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
    
    # Only add handler to root logger - propagation will handle the rest
    # This prevents duplicate messages from multiple handlers
    root_logger = logging.getLogger()
    if not any(isinstance(h, _UIBufferHandler) for h in root_logger.handlers):
        root_logger.addHandler(ui_handler)
    
    # Remove OpenTelemetry console handlers that output unwanted JSON logs
    # This needs to be called after any observability setup
    remove_opentelemetry_console_handlers()

    # Determine optional override for UI distribution directory
    if not ui_dist_dir:
        ui_dist_dir = os.environ.get("TOPAZ_UI_DIST_DIR") or None

    # Data directory is served via route handler below (not mounted) to allow better control
    # and security checks for file access

    # Serve UI from override dist directory if provided, otherwise serve packaged UI
    try:
        if ui_dist_dir and Path(ui_dist_dir).exists() and (Path(ui_dist_dir) / "index.html").exists():
            dist_root = Path(ui_dist_dir)
            logger.info("Serving UI from override dist directory: {}", dist_root)
            
            # Mount project static assets
            use_ui_static = Path(project_dir) / "ui" / "static"
            if use_ui_static.exists():
                app.mount("/static", StaticFiles(directory=str(use_ui_static)), name="static")
                logger.debug("Static files mounted from: {}", use_ui_static)

            @app.get("/")
            async def index():
                index_file = dist_root / "index.html"
                return FileResponse(str(index_file))
        else:
            # Serve packaged UI from topaz_agent_kit.ui.frontend
            try:
                ui_pkg = importlib.resources.files("topaz_agent_kit.ui.frontend")
                logger.info("Serving packaged UI from: {}", ui_pkg)
                
                # Mount project static assets
                use_ui_static = Path(project_dir) / "ui" / "static"
                if use_ui_static.exists():
                    app.mount("/static", StaticFiles(directory=str(use_ui_static)), name="static")
                    logger.debug("Static files mounted from: {}", use_ui_static)

                @app.get("/")
                async def index():
                    try:
                        index_file = ui_pkg / "index.html"
                        logger.debug("Serving packaged index.html from: {}", index_file)
                        # Read file content from importlib.resources (MultiplexedPath)
                        # FileResponse doesn't work with MultiplexedPath, so we read and return content
                        content = (ui_pkg / "index.html").read_bytes()
                        return Response(content=content, media_type="text/html")
                    except Exception as e:
                        logger.error("Failed to serve index.html: {}", e)
                        logger.error("Traceback: {}", traceback.format_exc())
                        return Response(
                            content=f"<html><body><h1>Error loading UI</h1><p>{str(e)}</p></body></html>",
                            media_type="text/html",
                            status_code=500
                        )
                    
                # Mount packaged static assets
                # Note: StaticFiles can't mount from importlib.resources directly
                # We'll handle static files via custom routes if needed
                # For now, skip mounting and let the UI handle asset loading via /static/ mount
                static_dir = ui_pkg / "_next"
                if static_dir.is_dir():
                    try:
                        # Try to get the actual file system path if possible
                        static_path = str(static_dir)
                        # Check if it's a real filesystem path (not MultiplexedPath)
                        if os.path.exists(static_path):
                            app.mount("/_next", StaticFiles(directory=static_path), name="next")
                            logger.debug("Packaged static files mounted from: {}", static_path)
                        else:
                            logger.warning("Cannot mount _next from packaged resources (MultiplexedPath), skipping")
                    except Exception as e:
                        logger.warning("Failed to mount _next static files: {}", e)
                
                # Mount packaged icons
                icons_dir = ui_pkg / "icons"
                if icons_dir.is_dir():
                    try:
                        icons_path = str(icons_dir)
                        if os.path.exists(icons_path):
                            app.mount("/icons", StaticFiles(directory=icons_path), name="icons")
                            logger.debug("Packaged icons mounted from: {}", icons_path)
                        else:
                            logger.warning("Cannot mount icons from packaged resources (MultiplexedPath), skipping")
                    except Exception as e:
                        logger.warning("Failed to mount icons: {}", e)
                
                # Mount packaged assets
                assets_dir = ui_pkg / "assets"
                if assets_dir.is_dir():
                    try:
                        assets_path = str(assets_dir)
                        if os.path.exists(assets_path):
                            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
                            logger.debug("Packaged assets mounted from: {}", assets_path)
                        else:
                            logger.warning("Cannot mount assets from packaged resources (MultiplexedPath), skipping")
                    except Exception as e:
                        logger.warning("Failed to mount assets: {}", e)
                    
            except Exception as e:
                logger.warning("Failed to mount packaged UI: {}", e)
                logger.error("Traceback: {}", traceback.format_exc())
                # Fallback to simple API response
                @app.get("/")
                async def index():
                    return JSONResponse({
                        "message": "Topaz Agent Kit API",
                        "note": "Packaged UI not available",
                        "endpoints": {
                            "manifest": "/manifest",
                            "health": "/health",
                            "turn": "/agui/turn",
                            "stream": "/agui/stream"
                        }
                    })
    except Exception as e:
        logger.warning("UI mounting failed: {}", e)
        logger.error("UI mounting traceback: {}", traceback.format_exc())
        # Ensure we always have a / endpoint, even if UI mounting completely fails
        @app.get("/")
        async def index_fallback():
            return JSONResponse({
                "message": "Topaz Agent Kit API",
                "note": "UI mounting failed",
                "error": str(e) if logger.isEnabledFor(logging.DEBUG) else "UI unavailable",
                "endpoints": {
                    "manifest": "/manifest",
                    "health": "/health",
                    "turn": "/agui/turn",
                    "stream": "/agui/stream"
                }
            })

    # Add global exception handler to catch and log all unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler to log all unhandled exceptions"""
        logger.error("Unhandled exception in {} {}: {}", request.method, request.url.path, exc)
        logger.error("Exception traceback: {}", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if logger.isEnabledFor(logging.DEBUG) else "An error occurred",
                "path": str(request.url.path)
            }
        )

    @app.get("/manifest")
    async def manifest():
        return JSONResponse(ui_manifest or {})

    @app.get("/api/ui_manifests/{pipeline_id}.yml")
    async def get_ui_manifest(pipeline_id: str):
        """Serve individual UI manifest files"""
        manifest_path = Path(project_dir) / "config" / "ui_manifests" / f"{pipeline_id}.yml"
        if manifest_path.exists():
            return FileResponse(str(manifest_path), media_type="text/yaml")
        else:
            return Response(status_code=404)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/sessions/new")
    async def create_new_session() -> JSONResponse:
        """Create a new chat session and return its ID."""
        try:
            session_id = orchestrator.create_session("fastapi")
            return JSONResponse({"session_id": session_id})
        except Exception as e:
            logger.error("Failed to create new session: {}", e)
            return JSONResponse({"error": "session_creation_failed"}, status_code=500)

    # Favicon and icon routes to eliminate 404s
    @app.get("/favicon.ico")
    async def favicon():
        # Try to serve from project static
        use_ui_static = Path(project_dir) / "ui" / "static"
        if use_ui_static.exists():
            icon_path = use_ui_static / "assets" / "topaz-logo.png"
            if icon_path.exists():
                logger.debug("Serving favicon from project static: {}", icon_path)
                response = FileResponse(str(icon_path), media_type="image/png")
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
            else:
                logger.debug("Favicon not found at project path: {}", icon_path)
        # Try packaged assets as fallback
        try:
            ui_pkg = importlib.resources.files("topaz_agent_kit.ui.frontend")
            assets_dir = ui_pkg / "assets"
            if assets_dir.is_dir():
                logo_path = assets_dir / "topaz-logo.png"
                if logo_path.is_file():
                    logger.debug("Serving favicon from packaged assets: {}", logo_path)
                    content = logo_path.read_bytes()
                    response = Response(content=content, media_type="image/png")
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
        except Exception as e:
            logger.debug("Failed to load packaged favicon: {}", e)
        # Return empty response if no icon found
        logger.warning("No favicon found, returning 204")
        return Response(status_code=204)
    
    @app.get("/apple-touch-icon.png")
    async def apple_touch_icon():
        # Try to serve from project static
        use_ui_static = Path(project_dir) / "ui" / "static"
        if use_ui_static.exists():
            icon_path = use_ui_static / "assets" / "topaz-logo.png"
            if icon_path.exists():
                response = FileResponse(str(icon_path))
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        # Try packaged assets as fallback
        try:
            ui_pkg = importlib.resources.files("topaz_agent_kit.ui.frontend")
            assets_dir = ui_pkg / "assets"
            if assets_dir.is_dir():
                logo_path = assets_dir / "topaz-logo.png"
                if logo_path.is_file():
                    content = logo_path.read_bytes()
                    response = Response(content=content, media_type="image/png")
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
        except Exception:
            pass
        # Return empty response if no icon found
        return Response(status_code=204)

    @app.get("/apple-touch-icon-precomposed.png")
    async def apple_touch_icon_precomposed():
        # Same as above for precomposed variant
        use_ui_static = Path(project_dir) / "ui" / "static"
        if use_ui_static.exists():
            icon_path = use_ui_static / "assets" / "topaz-logo.png"
            if icon_path.exists():
                response = FileResponse(str(icon_path))
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        return Response(status_code=204)
    
    # Explicit route for static assets favicon to ensure proper cache headers
    @app.get("/static/assets/topaz-logo.png")
    async def static_favicon():
        """Serve favicon from static assets with proper cache headers"""
        use_ui_static = Path(project_dir) / "ui" / "static"
        if use_ui_static.exists():
            icon_path = use_ui_static / "assets" / "topaz-logo.png"
            if icon_path.exists():
                logger.debug("Serving static favicon from: {}", icon_path)
                response = FileResponse(str(icon_path), media_type="image/png")
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        # Try packaged assets as fallback
        try:
            ui_pkg = importlib.resources.files("topaz_agent_kit.ui.frontend")
            assets_dir = ui_pkg / "assets"
            if assets_dir.is_dir():
                logo_path = assets_dir / "topaz-logo.png"
                if logo_path.is_file():
                    logger.debug("Serving static favicon from packaged assets: {}", logo_path)
                    content = logo_path.read_bytes()
                    response = Response(content=content, media_type="image/png")
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
        except Exception as e:
            logger.debug("Failed to load packaged static favicon: {}", e)
        logger.warning("Static favicon not found at /static/assets/topaz-logo.png")
        return Response(status_code=404)

    @app.post("/upload")
    async def upload_file(
        file: List[UploadFile] = File(default=[]),
        session_id: str = Form(None),
        message: str = Form(""),
        upload_intent: str = Form("session")  # "session" or "rag"
    ) -> JSONResponse:
        """Handle file upload with proper AG-UI events"""
        nonlocal current_session_id
        
        # Validate files
        if not file or len(file) == 0:
            return JSONResponse({"error": "No files provided"}, status_code=400)
        
        logger.info("File upload endpoint called: {} files, intent: {}", len(file), upload_intent)
        
        # Validate upload_intent
        if upload_intent not in ["session", "rag"]:
            return JSONResponse({"error": "Invalid upload_intent. Must be 'session' or 'rag'"}, status_code=400)
        
        # Validate all files have filenames
        for f in file:
            if not f.filename:
                return JSONResponse({"error": f"File {file.index(f)} has no filename"}, status_code=400)
        
        try:
            # Handle session ID
            # Require existing server-issued session_id
            if not session_id:
                return JSONResponse({"error": "missing_session_id"}, status_code=400)
            try:
                # Validate session exists
                if not orchestrator.get_session(session_id):
                    return JSONResponse({"error": "unknown_session_id"}, status_code=404)
                current_session_id = int(session_id)
            except ValueError:
                return JSONResponse({"error": "Invalid session_id format"}, status_code=400)
            
            # Use shared services
            file_storage, chroma_client, chat_storage, session_manager, db_manager = get_shared_services()
            
            # Process multiple files
            temp_file_paths = []
            original_filenames = []
            stored_files = []
            
            for f in file:
                # Get file content
                file_content = await f.read()
                
                # Determine file type from filename
                file_ext = Path(f.filename).suffix.lower().lstrip('.') if f.filename else 'unknown'
                
                if upload_intent == "session":
                    # Session upload: store in user_files/{session_id}/
                    storage_result = file_storage.store_file(
                        file_content=file_content,
                        filename=f.filename,
                        file_type=file_ext,
                        storage_type="session",
                        session_id=session_id
                    )
                    
                    logger.info("File stored for session: {} -> {}", f.filename, storage_result['file_id'])
                    
                    # For session uploads, we don't create temp files - just return the paths
                    stored_files.append({
                        "file_id": storage_result['file_id'],
                        "path": storage_result['path'],
                        "filename": f.filename
                    })
                    
                else:
                    # RAG upload: store in rag_files/ and create temp files for processing
                    storage_result = file_storage.store_file(
                        file_content=file_content,
                        filename=f.filename,
                        file_type=file_ext,
                        storage_type="rag"
                    )
                    
                    logger.info("File stored for RAG: {} -> {}", f.filename, storage_result['file_id'])
                    stored_files.append(storage_result)
                    
                    # Create temporary file for orchestrator to process
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{f.filename}") as temp_file:
                        temp_file.write(file_content)
                        temp_file_path = temp_file.name
                    
                    temp_file_paths.append(temp_file_path)
                    original_filenames.append(f.filename)
            
            if upload_intent == "session":
                # Session upload: validate message is provided
                if not message.strip():
                    return JSONResponse({
                        "error": "Message required for session uploads",
                        "upload_intent": "session"
                    }, status_code=400)
                
                # Return file paths for session upload (no processing)
                return JSONResponse({
                    "success": True,
                    "upload_intent": "session",
                    "message": "Files uploaded for session attachment",
                    "session_id": current_session_id,
                    "files": stored_files,
                    "user_message": message.strip()
                })
            
            else:
                # RAG upload: process with full ingestion
                try:
                    # Create session-specific run counter (same pattern as /agui/turn)
                    def get_next_run_counter():
                        current_count = session_run_counters.get(current_session_id, 0)
                        session_run_counters[current_session_id] = current_count + 1
                        return current_count
                    
                    # Ensure SSE queue exists for this session (same queue as /agui/turn)
                    q = agui_session_queues.setdefault(current_session_id, asyncio.Queue())
                    
                    # Create emitter for file upload events (same pattern as /agui/turn)
                    captured_events = []
                    
                    def emit_and_capture(evt: Dict[str, Any]) -> None:
                        try:
                            # Capture the event for pipeline_events (same pattern as CLI)
                            captured_events.append(evt)
                            
                            # Get or create AGUIService for this session (int key)
                            agui_service = agui_services.setdefault(current_session_id, AGUIService())
                            
                            # Convert event if needed (handles internal events like HITL)
                            agui_events = agui_service.convert_event(_json_safe(evt))
                            
                            # Enqueue each converted event to the SSE queue
                            for agui_evt in agui_events:
                                payload = f"data: {json.dumps(agui_evt)}\n\n"
                                q.put_nowait(payload)
                        except Exception as e:
                            logger.warning("AGUI emit failed: {}", e)
                    
                    # Use session-scoped emitter to maintain counters across turns (int key, same as /agui/turn)
                    emitter = agui_emitters.setdefault(current_session_id, AGUIEventEmitter(emit_and_capture, get_next_run_counter))
                    emitter._captured_events = captured_events
                    
                    # Process RAG files through assistant
                    assistant = agui_assistants.setdefault(
                        current_session_id,
                        Assistant(cfg, project_dir=project_dir, emitter=emitter, session_id=str(current_session_id)),
                    )
                    if current_session_id not in initialized_assistants:
                        await assistant.initialize()
                        initialized_assistants.add(current_session_id)
                    
                    result = await assistant.execute_assistant_agent(
                        user_input=message if message.strip() else "Process these files",
                        file_paths=temp_file_paths,
                        original_filenames=original_filenames,
                        upload_intent="rag",
                        mode="fastapi"
                    )
                    
                    # Handle AssistantResponse Pydantic model or fallback to dict
                    if isinstance(result, AssistantResponse):
                        success = result.success
                        assistant_response = result.assistant_response or ""
                        # Note: AssistantResponse doesn't have 'summary' field, use assistant_response
                        final_summary = assistant_response if assistant_response else "Unknown result"
                    elif isinstance(result, dict):
                        # Fallback for backward compatibility
                        success = result.get("success", False)
                        assistant_response = result.get("assistant_response", "")
                        summary = result.get("summary", "Unknown result")
                        final_summary = assistant_response if assistant_response else summary
                    else:
                        success = False
                        final_summary = "Unknown result"
                    
                    if success:
                        return JSONResponse({
                            "success": True,
                            "upload_intent": "rag",
                            "summary": final_summary,
                            "session_id": current_session_id,
                            "message": "File uploaded and processed successfully",
                            "files": stored_files
                        })
                    else:
                        return JSONResponse({
                            "success": False,
                            "upload_intent": "rag",
                            "error": final_summary,
                            "session_id": current_session_id
                        }, status_code=400)
                        
                finally:
                    # Clean up temporary files
                    for temp_file_path in temp_file_paths:
                        try:
                            os.unlink(temp_file_path)
                        except Exception:
                            pass
            
        except FileUploadError as e:
            logger.error("File upload validation failed: {}", e)
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            logger.error("File upload failed: {}", e)
            return JSONResponse({"error": f"Upload failed: {str(e)}"}, status_code=500)

    @app.get("/api/sessions/{session_id}/files")
    async def list_session_files(session_id: str):
        """List files for a specific session"""
        try:
            # Use shared services
            file_storage, chroma_client, chat_storage, session_manager, db_manager = get_shared_services()
            
            files = file_storage.list_session_files(session_id)
            
            return JSONResponse({
                "session_id": session_id,
                "files": files,
                "count": len(files)
            })
            
        except Exception as e:
            logger.error("Error listing session files for {}: {}", session_id, e)
            return JSONResponse({"error": f"Failed to list session files: {str(e)}"}, status_code=500)
    
    @app.get("/api/sessions/{session_id}/files/{file_id}")
    async def serve_session_file(session_id: str, file_id: str):
        """Serve a session file"""
        try:
            # Use shared services
            file_storage, chroma_client, chat_storage, session_manager, db_manager = get_shared_services()
            
            file_path = file_storage.get_file_path(file_id, session_id)
            if not file_path:
                return JSONResponse({"error": "File not found"}, status_code=404)
            
            file_info = file_storage.get_file_info(file_id)
            if not file_info:
                return JSONResponse({"error": "File info not found"}, status_code=404)
            
            file_content = file_storage.serve_file(file_id)
            if not file_content:
                return JSONResponse({"error": "File content not found"}, status_code=404)
            
            # Determine media type
            file_type = file_info.get("file_type", "").lower()
            media_type_map = {
                "pdf": "application/pdf",
                "txt": "text/plain",
                "doc": "application/msword",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "bmp": "image/bmp",
                "tiff": "image/tiff",
                "tif": "image/tiff",
                "webp": "image/webp"
            }
            media_type = media_type_map.get(file_type, "application/octet-stream")
            
            return Response(
                content=file_content,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"inline; filename=\"{file_info['filename']}\"",
                    "Cache-Control": "public, max-age=3600"
                }
            )
            
        except Exception as e:
            logger.error("Error serving session file {} from session {}: {}", file_id, session_id, e)
            return JSONResponse({"error": f"Failed to serve session file: {str(e)}"}, status_code=500)
    
    @app.delete("/api/sessions/{session_id}/files/{file_id}")
    async def delete_session_file(session_id: str, file_id: str):
        """Delete a session file"""
        try:
            # Use shared services
            file_storage, chroma_client, chat_storage, session_manager, db_manager = get_shared_services()
            
            success = file_storage.delete_session_file(file_id, session_id)
            
            if success:
                return JSONResponse({
                    "success": True,
                    "message": f"File {file_id} deleted from session {session_id}"
                })
            else:
                return JSONResponse({"error": "File not found or could not be deleted"}, status_code=404)
            
        except Exception as e:
            logger.error("Error deleting session file {} from session {}: {}", file_id, session_id, e)
            return JSONResponse({"error": f"Failed to delete session file: {str(e)}"}, status_code=500)

    @app.get("/api/reports/view")
    async def view_report(path: str):
        """Serve raw markdown report file"""
        try:
            # URL decode the path (FastAPI should do this automatically, but ensure it's decoded)
            from urllib.parse import unquote
            original_path = path
            path = unquote(path)
            
            # Security: Prevent directory traversal
            if '..' in path or path.startswith('/'):
                logger.warning("Invalid file path (security check): {}", path)
                return JSONResponse({"error": "Invalid file path"}, status_code=400)
            
            # Normalize the path - remove leading slashes
            path = path.lstrip('/')
            
            # Build the full report path
            report_path = Path(project_dir) / "data" / path
            
            logger.debug("Serving report - original: {}, decoded: {}, normalized: {}, resolved: {}", 
                        original_path, unquote(original_path), path, report_path)
            
            if not report_path.exists():
                logger.warning("Report file not found: {} (original path: {}, decoded: {})", 
                              report_path, original_path, path)
                # List available files in the reports directory for debugging
                reports_dir = Path(project_dir) / "data" / "tci" / "reports"
                if reports_dir.exists():
                    available_files = [f.name for f in reports_dir.glob("*.md")]
                    if available_files:
                        logger.info("Available report files in {}: {}", reports_dir, available_files)
                    else:
                        logger.warning("Reports directory exists but is empty: {}", reports_dir)
                else:
                    logger.warning("Reports directory does not exist: {}", reports_dir)
                return JSONResponse({"error": "Report file not found"}, status_code=404)
            
            # Ensure the file is within the data directory
            try:
                report_path.resolve().relative_to(Path(project_dir) / "data")
            except ValueError:
                return JSONResponse({"error": "Invalid file path"}, status_code=400)
            
            # Only allow .md files
            if not path.endswith('.md'):
                return JSONResponse({"error": "Only markdown files are supported"}, status_code=400)
            
            # Read and return markdown content
            return FileResponse(
                path=str(report_path),
                media_type="text/markdown",
                headers={
                    "Cache-Control": "public, max-age=3600"
                }
            )
        except Exception as e:
            logger.error("Error serving report {}: {}", path, e)
            return JSONResponse({"error": f"Failed to serve report: {str(e)}"}, status_code=500)

    @app.get("/api/readme")
    async def get_readme():
        """Serve README.md from project root or repository root"""
        try:
            # First try project directory
            readme_path = Path(project_dir) / "README.md"
            if not readme_path.exists():
                # Try repository root (go up from project_dir to find README.md)
                # project_dir is typically like .../projects/ensemble
                # So we go up two levels to get to repository root
                repo_root = Path(project_dir).parent.parent
                readme_path = repo_root / "README.md"
            
            if readme_path.exists():
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return Response(
                    content=content,
                    media_type="text/markdown",
                    headers={
                        "Cache-Control": "public, max-age=3600"
                    }
                )
            else:
                return JSONResponse({"error": "README.md not found in project root or repository root"}, status_code=404)
        except Exception as e:
            logger.error("Error serving README: {}", e)
            return JSONResponse({"error": f"Failed to serve README: {str(e)}"}, status_code=500)


    @app.get("/api/documents")
    async def list_documents():
        """List all documents with combined metadata from ChromaDB and chat.db"""
        try:
            
            
            # Use shared services (initialized once, reused across requests)
            file_storage, chroma_client, chat_storage, session_manager, db_manager = get_shared_services()
            
            # Get documents from ChromaDB
            documents = []
            try:
                collections = chroma_client.list_collections()
                
                # Process both documents and images collections
                collection_names = ["documents", "images"]
                for collection_name in collection_names:
                    if any(c.name == collection_name for c in collections):
                        collection = chroma_client.get_collection(collection_name)
                        all_docs = collection.get()
                        
                        # Group by filename to get unique documents
                        doc_groups = {}
                        for i, metadata in enumerate(all_docs.get("metadatas", [])):
                            filename = metadata.get("file_name", "unknown")
                            if filename not in doc_groups:
                                doc_groups[filename] = {
                                    "filename": filename,
                                    "file_size": metadata.get("file_size", 0),
                                    "upload_date": metadata.get("upload_date", ""),
                                    "file_hash": metadata.get("file_hash", ""),
                                    "chunks_count": 0,
                                    "collection_type": collection_name
                                }
                            doc_groups[filename]["chunks_count"] += 1
                        
                        # Get analysis results from chat.db
                        for filename, doc_info in doc_groups.items():
                            # Get analysis results
                            analysis_results = db_manager.get_available_content_by_filename(filename)
                            
                            # Get file storage info
                            stored_files = file_storage.list_files()
                            file_storage_info = None
                            for stored_file in stored_files:
                                if stored_file["filename"] == filename:
                                    file_storage_info = stored_file
                                    break
                            
                            # Combine all information
                            document = {
                                "id": file_storage_info["file_id"] if file_storage_info else f"unknown_{filename}",
                                "name": filename,
                                "type": file_storage_info["file_type"] if file_storage_info else "unknown",
                                "size": doc_info["file_size"],
                                "uploadDate": doc_info["upload_date"],
                                "fileHash": doc_info["file_hash"],
                                "chunksCount": doc_info["chunks_count"],
                                "hasStorage": file_storage_info is not None,
                                "summary": analysis_results.get("summary") if analysis_results else None,
                                "topics": analysis_results.get("topics", []) if analysis_results else [],
                                "exampleQuestions": analysis_results.get("example_questions", []) if analysis_results else []
                            }
                            documents.append(document)
                    
                    # Sort by upload date (newest first)
                    documents.sort(key=lambda x: x["uploadDate"], reverse=True)
                    
            except Exception as e:
                logger.warning("Error accessing ChromaDB: {}", e)
            
            return JSONResponse({
                "documents": documents,
                "total": len(documents)
            })
            
        except Exception as e:
            logger.error("Error listing documents: {}", e)
            return JSONResponse({"error": f"Failed to list documents: {str(e)}"}, status_code=500)
    
    @app.get("/api/documents/{document_id}/file")
    async def serve_document_file(document_id: str):
        """Serve original file for preview"""
        try:
            # Get files path from orchestrator config
            rag_files_path = orchestrator.validated_config.rag_files_path if orchestrator.validated_config else "./data/rag_files"
            user_files_path = orchestrator.validated_config.user_files_path if orchestrator.validated_config else "./data/user_files"
            
            if not Path(rag_files_path).is_absolute():
                rag_files_path = str(Path(project_dir) / rag_files_path)
            if not Path(user_files_path).is_absolute():
                user_files_path = str(Path(project_dir) / user_files_path)
            
            file_storage = FileStorageService(rag_files_path, user_files_path)
            
            # First try to serve by document_id directly
            file_content = file_storage.serve_file(document_id)
            
            # If not found, try to find by document name
            if file_content is None:
                # List all files and find by name
                files = file_storage.list_files()
                for file_info in files:
                    if file_info["filename"] == document_id:
                        file_content = file_storage.serve_file(file_info["id"])
                        break
            
            if file_content is None:
                return JSONResponse({"error": "File not found"}, status_code=404)
            
            # Get file info for content type
            # Use the actual file_id that was found
            actual_file_id = document_id
            if file_content is not None:
                # If we found the file by name, get the actual file_id
                files = file_storage.list_files()
                for file_info in files:
                    if file_info["filename"] == document_id:
                        actual_file_id = file_info["id"]
                        break
            
            # Get file info using the correct file_id
            file_info = file_storage.get_file_info(actual_file_id)
            if not file_info:
                # If get_file_info fails, try to build file info from the file path
                files = file_storage.list_files()
                for file_info_item in files:
                    if file_info_item["filename"] == document_id:
                        file_info = file_info_item
                        break
                
                if not file_info:
                    return JSONResponse({"error": "File info not found"}, status_code=404)
            
            # Determine content type
            content_type_map = {
                'pdf': 'application/pdf',
                'txt': 'text/plain',
                'md': 'text/markdown',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'csv': 'text/csv',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'json': 'application/json',
                'html': 'text/html',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'bmp': 'image/bmp',
                'tiff': 'image/tiff',
                'tif': 'image/tiff',
                'webp': 'image/webp'
            }
            
            content_type = content_type_map.get(file_info["file_type"], "application/octet-stream")
            
            return Response(
                content=file_content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename=\"{file_info['filename']}\"",
                    "Cache-Control": "public, max-age=3600"
                }
            )
            
        except Exception as e:
            logger.error("Error serving file {}: {}", document_id, e)
            return JSONResponse({"error": f"Failed to serve file: {str(e)}"}, status_code=500)
    
    @app.get("/api/documents/{document_id}/highlighted")
    async def serve_highlighted_document(
        document_id: str,
        text: str,
        page: int = None,
        color: str = "yellow"
    ):
        """
        Serve a PDF document with highlighted text using PyMuPDF
        
        Args:
            document_id: Document ID
            text: Text to highlight
            page: Specific page number (optional)
            color: Highlight color (yellow, green, red, blue)
        """
        try:
            logger.debug("Serving highlighted PDF for document {}", document_id)
            logger.debug("   Text to highlight: {}", text)
            logger.debug("   Page: {}", page)
            logger.debug("   Color: {}", color)
            
            # Use shared services (initialized once, reused across requests)
            file_storage, chroma_client, chat_storage, session_manager, db_manager = get_shared_services()
            
            # Get file info from file storage
            file_info = file_storage.get_file_info(document_id)
            if not file_info:
                return JSONResponse({"error": "Document not found"}, status_code=404)
            
            # Check if it's a PDF
            if file_info["file_type"] != "pdf":
                return JSONResponse({"error": "Highlighting only supported for PDF files"}, status_code=400)
            
            # Get original file content
            file_content = file_storage.serve_file(document_id)
            if not file_content:
                return JSONResponse({"error": "File content not found"}, status_code=404)
            
            # Check cache first
            logger.debug("🔍 Checking cache for document {} with text '{}' and page {}", document_id, text, page)
            cached_content = pdf_highlighter.get_cached_highlighted_pdf(
                document_id, text, page
            )
            
            if cached_content:
                logger.debug("✅ CACHE HIT: Serving cached highlighted PDF for document {}", document_id)
                highlighted_content = cached_content
            else:
                logger.debug("❌ CACHE MISS: Generating new highlighted PDF for document {} with text '{}'", document_id, text)
                # Convert color string to RGB tuple
                color_map = {
                    "yellow": (1, 1, 0),
                    "green": (0, 1, 0),
                    "red": (1, 0, 0),
                    "blue": (0, 0, 1),
                    "orange": (1, 0.5, 0),
                    "purple": (0.5, 0, 1),
                    "pink": (1, 0.5, 0.8),
                    "cyan": (0, 1, 1)
                }
                highlight_color = color_map.get(color.lower(), (1, 1, 0))  # Default to yellow
                
                # Generate highlighted PDF
                logger.debug("Generating highlighted PDF for document {} with text '{}'", document_id, text)
                highlighted_content = pdf_highlighter.highlight_pdf(
                    file_content, text, highlight_color, page
                )
                
                if not highlighted_content:
                    return JSONResponse({"error": "Failed to highlight PDF"}, status_code=500)
                
                # Cache the result
                pdf_highlighter.cache_highlighted_pdf(
                    document_id, text, highlighted_content, page
                )
            
            # Return highlighted PDF
            return Response(
                content=highlighted_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; filename=\"{file_info['filename']}_highlighted.pdf\"",
                    "Cache-Control": "public, max-age=3600"
                }
            )
            
        except Exception as e:
            logger.error("Error serving highlighted file {}: {}", document_id, e)
            return JSONResponse({"error": f"Failed to serve highlighted file: {str(e)}"}, status_code=500)
    
    @app.delete("/api/documents/{document_id}")
    async def delete_document(document_id: str):
        """Delete document from all storage locations"""
        try:
            # Initialize services
            # Get files path from orchestrator config
            rag_files_path = orchestrator.validated_config.rag_files_path if orchestrator.validated_config else "./data/rag_files"
            user_files_path = orchestrator.validated_config.user_files_path if orchestrator.validated_config else "./data/user_files"
            
            if not Path(rag_files_path).is_absolute():
                rag_files_path = str(Path(project_dir) / rag_files_path)
            if not Path(user_files_path).is_absolute():
                user_files_path = str(Path(project_dir) / user_files_path)
            
            file_storage = FileStorageService(rag_files_path, user_files_path)
            
            # Get file info first
            file_info = file_storage.get_file_info(document_id)
            filename = None
            actual_file_id = None
            
            if file_info:
                # Document exists in file storage
                filename = file_info["filename"]
                actual_file_id = document_id
            else:
                # Document might not exist in file storage but could exist in ChromaDB/chat.db
                # Check if document_id starts with "unknown_" and extract filename
                if document_id.startswith("unknown_"):
                    filename = document_id[8:]  # Remove "unknown_" prefix
                    # Try to find the actual file ID by searching for files with this filename
                    try:
                        stored_files = file_storage.list_files()
                        for file_data in stored_files:
                            if file_data["filename"] == filename:
                                actual_file_id = file_data["id"]
                                break
                    except Exception as e:
                        logger.warning("Failed to search for file by filename: {}", e)
                else:
                    return JSONResponse({"error": "Document not found"}, status_code=404)
            deletion_results = {
                "file_storage": False,
                "chromadb": False,
                "chat_db": False
            }
            
            # 1. Delete from file storage
            try:
                if actual_file_id:
                    deletion_results["file_storage"] = file_storage.delete_file(actual_file_id)
                    logger.info("Deleted file from storage: {} (ID: {})", filename, actual_file_id)
                else:
                    # File doesn't exist in storage, mark as already deleted
                    deletion_results["file_storage"] = True
                    logger.info("File not found in storage, considering it already deleted: {}", filename)
            except Exception as e:
                logger.warning("Failed to delete from file storage: {}", e)
            
            # 2. Delete from ChromaDB
            try:
                chromadb_path = orchestrator.validated_config.chromadb_path if orchestrator.validated_config else "./data/chroma_db"
                if not Path(chromadb_path).is_absolute():
                    chromadb_path = str(Path(project_dir) / chromadb_path)
                
                chroma_client = PersistentClient(path=chromadb_path)
                collections = chroma_client.list_collections()
                
                # Delete from both documents and images collections
                collection_names = ["documents", "images"]
                chromadb_deleted = False
                
                for collection_name in collection_names:
                    if any(c.name == collection_name for c in collections):
                        collection = chroma_client.get_collection(collection_name)
                        # Delete by file_name metadata
                        result = collection.delete(where={"file_name": filename})
                        if result:
                            chromadb_deleted = True
                            logger.info("Deleted from ChromaDB collection '{}': {}", collection_name, filename)
                
                deletion_results["chromadb"] = chromadb_deleted
                    
            except Exception as e:
                logger.warning("Failed to delete from ChromaDB: {}", e)
            
            # 3. Delete from chat.db
            try:
                chatdb_path = orchestrator.validated_config.chatdb_path if orchestrator.validated_config else "./data/chat.db"
                if not Path(chatdb_path).is_absolute():
                    chatdb_path = str(Path(project_dir) / chatdb_path)
                
                chat_storage = ChatStorage(chatdb_path)
                session_manager = SessionManager(chat_storage)
                db_manager = DatabaseManager(chat_storage, session_manager)
                
                # Delete available content by filename
                success = db_manager.delete_available_content_by_filename(filename)
                deletion_results["chat_db"] = success
                
            except Exception as e:
                logger.warning("Failed to delete from chat.db: {}", e)
            
            # Check if any deletion succeeded
            if any(deletion_results.values()):
                return JSONResponse({
                    "success": True,
                    "message": f"Document '{filename}' deleted",
                    "deletion_results": deletion_results
                })
            else:
                return JSONResponse({
                    "success": False,
                    "error": "Failed to delete document from any storage location",
                    "deletion_results": deletion_results
                }, status_code=500)
            
        except Exception as e:
            logger.error("Error deleting document {}: {}", document_id, e)
            return JSONResponse({"error": f"Failed to delete document: {str(e)}"}, status_code=500)
    
    # -----------------------------
    # Scripts Endpoints
    # -----------------------------
    
    def _load_scripts_registry(scripts_dir: Path) -> Dict[str, Any]:
        """Load scripts registry from scripts.yml if it exists"""
        registry_file = scripts_dir / "scripts.yml"
        if registry_file.exists():
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning("Failed to load scripts registry: {}", e)
        return {}
    
    def _find_script_in_registry(filename: str, registry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find script entry in registry by filename"""
        scripts = registry.get("scripts", [])
        for script in scripts:
            if script.get("filename") == filename:
                return script
        return None
    
    @app.get("/api/scripts")
    async def list_scripts():
        """List all executable scripts from project_dir/scripts folder"""
        try:
            scripts_dir = Path(project_dir) / "scripts"
            
            if not scripts_dir.exists():
                return JSONResponse({"scripts": [], "total": 0})
            
            # Load registry
            registry = _load_scripts_registry(scripts_dir)
            
            # Scan for executable files
            executable_extensions = {'.py', '.ps1', '.sh', '.bat', '.cmd'}
            scripts_list = []
            
            for script_path in scripts_dir.rglob("*"):
                if script_path.is_file() and script_path.suffix.lower() in executable_extensions:
                    # Skip __pycache__ and other hidden directories
                    if '__pycache__' in script_path.parts:
                        continue
                    
                    # Get relative path from scripts_dir
                    rel_path = script_path.relative_to(scripts_dir)
                    filename = str(rel_path).replace('\\', '/')  # Normalize path separators
                    
                    # Get registry entry
                    registry_entry = _find_script_in_registry(filename, registry)
                    
                    # Get file stats
                    stat = script_path.stat()
                    
                    script_info = {
                        "filename": filename,
                        "name": registry_entry.get("name", script_path.stem) if registry_entry else script_path.stem,
                        "description": registry_entry.get("description", "") if registry_entry else "",
                        "category": registry_entry.get("category", "Other") if registry_entry else "Other",
                        "extension": script_path.suffix.lower(),
                        "path": str(script_path),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "parameters": registry_entry.get("parameters", []) if registry_entry else []
                    }
                    scripts_list.append(script_info)
            
            # Sort by name
            scripts_list.sort(key=lambda x: x["name"].lower())
            
            return JSONResponse({
                "scripts": scripts_list,
                "total": len(scripts_list)
            })
            
        except Exception as e:
            logger.error("Error listing scripts: {}", e)
            return JSONResponse({"error": f"Failed to list scripts: {str(e)}"}, status_code=500)
    
    @app.post("/api/scripts/{script_name:path}/run")
    async def run_script(script_name: str, request: Request):
        """Execute a script with optional parameters"""
        try:
            scripts_dir = Path(project_dir) / "scripts"
            script_path = scripts_dir / script_name
            
            # Security check: ensure script is within scripts directory
            try:
                script_path.resolve().relative_to(scripts_dir.resolve())
            except ValueError:
                return JSONResponse({"error": "Invalid script path"}, status_code=400)
            
            if not script_path.exists() or not script_path.is_file():
                return JSONResponse({"error": "Script not found"}, status_code=404)
            
            # Get parameters from request body
            body = await request.json()
            parameters = body.get("parameters", {})
            
            # Load registry to get parameter definitions
            registry = _load_scripts_registry(scripts_dir)
            registry_entry = _find_script_in_registry(script_name, registry)
            
            # Build command based on file extension
            extension = script_path.suffix.lower()
            start_time = time.time()
            
            if extension == '.py':
                # Use current Python interpreter
                import sys
                python_exe = sys.executable
                cmd = [python_exe, str(script_path)]
                # Add parameters as command-line arguments
                # Check if parameter is a flag (boolean) from registry
                for param_name, param_value in parameters.items():
                    # Check if this is a flag parameter
                    is_flag = False
                    if registry_entry:
                        param_def = next(
                            (p for p in registry_entry.get("parameters", []) if p.get("name") == param_name),
                            None
                        )
                        if param_def and param_def.get("type") == "flag":
                            is_flag = True
                    
                    if is_flag:
                        # For flags, only add the flag if value is truthy
                        if param_value and str(param_value).lower() in ("true", "1", "yes", "on"):
                            cmd.append(f"--{param_name}")
                    else:
                        # For regular parameters, add both name and value
                        if param_value:  # Only add non-empty values
                            cmd.extend([f"--{param_name}", str(param_value)])
            elif extension == '.ps1':
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
                # PowerShell parameters
                for param_name, param_value in parameters.items():
                    if param_value:
                        cmd.extend([f"-{param_name}", str(param_value)])
            elif extension in ['.sh', '.bat', '.cmd']:
                cmd = [str(script_path)]
                # Add parameters
                for param_name, param_value in parameters.items():
                    if param_value:
                        cmd.extend([str(param_value)])
            else:
                return JSONResponse({"error": f"Unsupported script type: {extension}"}, status_code=400)
            
            # Execute script
            # Scripts expect to run from repository root (where pyproject.toml is)
            # because they use paths like "projects/ensemble/data/..."
            repo_root = find_repository_root(Path(project_dir))
            logger.debug("Running script from repository root: {} (project_dir: {})", repo_root, project_dir)
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(repo_root),  # Working directory is repository root (scripts expect this)
                    env=os.environ.copy()  # Use same environment as FastAPI app
                )
                
                # Wait with timeout (5 minutes)
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return JSONResponse({
                        "success": False,
                        "error": "Script execution timed out after 5 minutes",
                        "return_code": -1,
                        "stdout": "",
                        "stderr": "",
                        "execution_time": time.time() - start_time
                    }, status_code=408)
                
                execution_time = time.time() - start_time
                return_code = process.returncode
                
                stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
                stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
                
                return JSONResponse({
                    "success": return_code == 0,
                    "return_code": return_code,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "execution_time": round(execution_time, 2)
                })
                
            except Exception as e:
                logger.error("Error executing script {}: {}", script_name, e)
                return JSONResponse({
                    "success": False,
                    "error": str(e),
                    "return_code": -1,
                    "stdout": "",
                    "stderr": "",
                    "execution_time": time.time() - start_time
                }, status_code=500)
            
        except Exception as e:
            logger.error("Error running script {}: {}", script_name, e)
            return JSONResponse({"error": f"Failed to run script: {str(e)}"}, status_code=500)
    
    @app.get("/history")
    async def get_history():
        # Return sessions summary: id, count, title (first q), last intent
        out = []
        for sid, turns in sessions.items():
            if not turns:
                continue
            title = (turns[0].get("q") or "")[:80]
            last_intent = turns[-1].get("t")
            out.append({"id": sid, "title": title, "count": len(turns), "t": last_intent})
        # Sort by id desc (newest first)
        out.sort(key=lambda x: x.get("id", 0), reverse=True)
        return JSONResponse(out)

    @app.get("/history/item")
    async def get_history_item(id: int) -> JSONResponse:
        sid = int(id)
        turns = sessions.get(sid) or []
        if turns:
            return JSONResponse({"id": sid, "turns": turns})
        # Fallback: reconstruct from per-session files
        try:
            hist_dir = (Path(project_dir) / "data" / "history")
            # Prefer pretty JSON if available, else JSONL
            jf = hist_dir / f"{sid}.json"
            if jf.exists():
                arr = json.loads(jf.read_text(encoding="utf-8") or "[]")
                return JSONResponse({"id": sid, "turns": arr or []})
            lf = hist_dir / f"{sid}.jsonl"
            if lf.exists():
                found: list[dict] = []
                for line in lf.read_text(encoding="utf-8").splitlines():
                    try:
                        obj = json.loads(line)
                        found.append(obj)
                    except Exception:
                        continue
                if found:
                    return JSONResponse({"id": sid, "turns": found})
        except Exception:
            pass
        return JSONResponse({"error": "not_found"}, status_code=404)

    @app.post("/history/delete")
    async def delete_history_item(req: Request) -> JSONResponse:
        try:
            body = await req.json()
            target_id = int(body.get("id"))
        except Exception:
            return JSONResponse({"error": "bad_request"}, status_code=400)
        # Remove from memory
        try:
            idx = next((i for i, it in enumerate(history) if int(it.get("id", -1)) == target_id), -1)
            if idx >= 0:
                history.pop(idx)
        except Exception:
            pass
        # Delete per-session files and remove from summary
        try:
            # Remove from sessions
            if target_id in sessions:
                sessions.pop(target_id, None)
            hist_dir = (Path(project_dir) / "data" / "history")
            try:
                (hist_dir / f"{target_id}.json").unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass
            try:
                (hist_dir / f"{target_id}.jsonl").unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass
        except Exception:
            pass
        return JSONResponse({"ok": True})

    @app.post("/session/new")
    async def new_session() -> JSONResponse:
        nonlocal current_session_id
        current_session_id = int(time.time() * 1000)
        sessions.setdefault(current_session_id, [])
        return JSONResponse({"id": current_session_id})

    @app.post("/session/select")
    async def select_session(req: Request) -> JSONResponse:
        nonlocal current_session_id
        try:
            body = await req.json()
            sid = int(body.get("id"))
        except Exception:
            return JSONResponse({"error": "bad_request"}, status_code=400)
        current_session_id = sid
        sessions.setdefault(current_session_id, [])
        logger.info("Selected session {} for subsequent turns", current_session_id)
        return JSONResponse({"ok": True, "id": current_session_id})

    # === SQLite Chat Storage API Endpoints ===
    
    @app.get("/api/sessions")
    async def get_chat_sessions() -> JSONResponse:
        """Get all chat sessions from SQLite database"""
        try:
            sessions_data = orchestrator.get_all_sessions('active')
            sessions_list = []
            
            for session in sessions_data:
                # Get turn count for each session
                turns = orchestrator.get_turns_for_session(session.id)
                
                # Use title from database (generated by assistant or fallback)
                title = session.title if hasattr(session, 'title') and session.title else "New chat"
                
                # Get pinned status (default to False if not set)
                pinned = getattr(session, 'pinned', False)
                if isinstance(pinned, int):
                    pinned = bool(pinned)
                
                # Get pinned_order (default to 0 if not set)
                pinned_order = getattr(session, 'pinned_order', 0)
                if not isinstance(pinned_order, int):
                    pinned_order = 0
                
                sessions_list.append({
                    "id": session.id,
                    "title": title,
                    "created_at": session.created_at.isoformat(),
                    "last_accessed": session.last_accessed.isoformat(),
                    "turn_count": len(turns),
                    "status": session.status,
                    "pinned": pinned,
                    "pinned_order": pinned_order
                })
            
            # Sort by last_accessed descending
            sessions_list.sort(key=lambda x: x["last_accessed"], reverse=True)
            
            return JSONResponse({"sessions": sessions_list})
            
        except Exception as e:
            logger.error("Failed to get chat sessions: {}", e)
            return JSONResponse({"error": "Failed to load sessions"}, status_code=500)
    
    @app.get("/api/sessions/{session_id}")
    async def get_chat_session(session_id: str) -> JSONResponse:
        """Get specific chat session with all turns from SQLite database"""
        try:
            # Get session
            session = orchestrator.get_session(session_id)
            if not session:
                return JSONResponse({"error": "Session not found"}, status_code=404)
            
            # Get all turns for this session
            turns = orchestrator.get_turns_for_session(session_id)
            
            # Convert turns to the format expected by the UI
            turns_data = []
            for turn in turns:
                turn_data = {
                    "turn_id": turn.turn_id,
                    "turn_number": turn.turn_number,
                    "pipeline_id": turn.pipeline_id,
                    "run_id": turn.run_id,  # Add run_id for feedback mapping
                    "status": turn.status,
                    "started_at": turn.started_at.isoformat() if turn.started_at else None,
                    "error_message": turn.error_message,
                    "feedback": turn.feedback  # Add feedback data (already parsed in ChatTurn)
                }
                turns_data.append(turn_data)
            
            # Use title from database (generated by assistant or fallback)
            title = session.title if hasattr(session, 'title') and session.title else "New chat"
            
            return JSONResponse({
                "session": {
                    "id": session.id,
                    "title": title,
                    "created_at": session.created_at.isoformat(),
                    "last_accessed": session.last_accessed.isoformat(),
                    "status": session.status
                },
                "turns": turns_data
            })
            
        except Exception as e:
            logger.error("Failed to get chat session {}: {}", session_id, e)
            return JSONResponse({"error": "Failed to load session"}, status_code=500)
    
    @app.get("/api/sessions/{session_id}/entries")
    async def get_session_entries(session_id: str) -> JSONResponse:
        """Get all entries for a session (merged from all turns)"""
        try:
            # Get all entries for the session (merged from all turns)
            all_entries = orchestrator.get_all_session_entries(session_id)
            
            # Extract pipeline names from workflow entries
            pipeline_names: Dict[str, str] = {}
            for entry in all_entries:
                if entry.get("kind") == "workflow" and entry.get("runId"):
                    pipeline_name = entry.get("pipelineName", "Unknown")
                    pipeline_names[entry["runId"]] = pipeline_name
            
            return JSONResponse({
                "entries": all_entries,
                "pipelineNames": pipeline_names
            })
            
        except Exception as e:
            logger.error("Failed to get session entries {}: {}", session_id, e)
            return JSONResponse({"error": "Failed to load entries"}, status_code=500)
    
    @app.post("/api/runs/{run_id}/entries")
    async def save_run_entries(run_id: str, request: Request) -> JSONResponse:
        """Save entries for a run (called from frontend)"""
        try:
            body = await request.json()
            entries = body.get("entries", [])
            
            if not isinstance(entries, list):
                return JSONResponse({"error": "entries must be a list"}, status_code=400)
            
            logger.debug("Saving {} entries for run_id: {}", len(entries), run_id)
            
            # Get turn by run_id via orchestrator
            turn = orchestrator.get_turn_by_run_id(run_id)
            if not turn:
                logger.warning("Turn not found for run_id: {}", run_id)
                return JSONResponse({"error": "Turn not found for run_id", "run_id": run_id}, status_code=404)
            
            turn_id = turn.turn_id
            if not turn_id:
                logger.warning("Turn ID not found for run_id: {}", run_id)
                return JSONResponse({"error": "Turn ID not found", "run_id": run_id}, status_code=404)
            
            logger.debug("Found turn_id {} for run_id {}", turn_id, run_id)
            
            # Update entries for this turn
            success = orchestrator.update_turn_entries(turn_id, entries)
            
            if success:
                logger.info("Saved {} entries for run {} (turn {})", len(entries), run_id, turn_id)
                return JSONResponse({"ok": True, "entries_count": len(entries), "turn_id": turn_id})
            else:
                logger.error("Failed to update entries for turn_id: {}", turn_id)
                return JSONResponse({"error": "Failed to save entries", "turn_id": turn_id}, status_code=500)
            
        except Exception as e:
            logger.error("Failed to save run entries {}: {}", run_id, e, exc_info=True)
            return JSONResponse({"error": "Failed to save entries", "details": str(e)}, status_code=500)

    @app.post("/api/feedback")
    async def submit_feedback(request: Request) -> JSONResponse:
        """Store feedback for a turn"""
        try:
            body = await request.json()
            run_id = body.get("run_id")
            feedback_type = body.get("feedback_type")
            comment = body.get("comment", "")
            
            if not run_id:
                return JSONResponse({"error": "run_id is required"}, status_code=400)
            
            if feedback_type not in ["up", "down"]:
                return JSONResponse({"error": "feedback_type must be 'up' or 'down'"}, status_code=400)
            
            # Get turn by run_id
            turn = orchestrator.get_turn_by_run_id(run_id)
            
            if not turn:
                return JSONResponse({"error": "Turn not found for run_id"}, status_code=404)
            
            # Get turn_id and status from the turn object (ChatTurn dataclass)
            turn_id = turn.turn_id
            current_status = turn.status if turn.status else 'completed'
            
            # Prepare feedback data
            from datetime import datetime
            feedback_data = {
                "type": feedback_type,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update turn with feedback using update_turn_status
            # Keep the current status, just add feedback in updates
            success = orchestrator.update_turn_status(turn_id, current_status, {"feedback": feedback_data})
            
            if success:
                logger.info("Stored feedback for turn {} (run_id: {}): {}", turn_id, run_id, feedback_type)
                return JSONResponse({"ok": True, "turn_id": turn_id, "run_id": run_id})
            else:
                logger.error("Failed to store feedback for turn {}", turn_id)
                return JSONResponse({"error": "Failed to store feedback"}, status_code=500)
            
        except Exception as e:
            logger.error("Failed to submit feedback: {}", e, exc_info=True)
            return JSONResponse({"error": "Failed to submit feedback", "details": str(e)}, status_code=500)

    @app.post("/api/sessions/{session_id}/restore")
    async def restore_chat_session(session_id: str) -> JSONResponse:
        """Restore a chat session and set it as current"""
        try:
            # Use session manager to restore the session
            restore_result = orchestrator.restore_session(session_id)
            
            # Set as current session
            nonlocal current_session_id
            current_session_id = int(session_id) if session_id.isdigit() else None
            
            # Get session title from restored session
            session = restore_result.session
            title = session.title if hasattr(session, 'title') and session.title else "New chat"
            
            return JSONResponse({
                "ok": True,
                "session_id": session_id,
                "title": title,
                "turns_restored": len(restore_result.turns)
            })
            
        except Exception as e:
            logger.error("Failed to restore chat session {}: {}", session_id, e)
            return JSONResponse({"error": "Failed to restore session"}, status_code=500)

    @app.delete("/api/sessions/{session_id}")
    async def delete_chat_session(session_id: str) -> JSONResponse:
        """Delete a chat session and all associated turns from chat.db, plus cleanup session files"""
        try:
            # Use shared services
            file_storage, chroma_client, chat_storage, session_manager, db_manager = get_shared_services()
            
            # Verify session exists before deletion
            session = orchestrator.get_session(session_id)
            if not session:
                return JSONResponse({"error": "Session not found"}, status_code=404)
            
            # Delete session from database (this also deletes all associated turns)
            success = session_manager.delete_session(session_id)
            
            if not success:
                logger.error("Failed to delete session {} from database", session_id)
                return JSONResponse({"error": "Failed to delete session from database"}, status_code=500)
            
            # Clean up session files
            try:
                file_storage.cleanup_session_files(session_id)
            except Exception as e:
                logger.warning("Failed to cleanup session files for {}: {}", session_id, e)
                # Don't fail the request if file cleanup fails
            
            # Clear session from in-memory orchestrator state if it exists
            try:
                nonlocal current_session_id
                if current_session_id == int(session_id) if session_id.isdigit() else None:
                    current_session_id = None
                
                # Clean up AG-UI session state
                agui_session_queues.pop(int(session_id), None)
                hitl_waiters.pop(int(session_id), None)
                agui_services.pop(int(session_id), None)
                session_run_counters.pop(int(session_id), None)
                agui_emitters.pop(int(session_id), None)
                agui_assistants.pop(int(session_id), None)
                initialized_assistants.discard(int(session_id))
            except (ValueError, KeyError):
                pass  # Session ID might not be numeric or not in memory state
            
            logger.info("Successfully deleted session {} and all associated data", session_id)
            return JSONResponse({
                "ok": True,
                "session_id": session_id,
                "message": "Session deleted successfully"
            })
            
        except Exception as e:
            logger.error("Failed to delete chat session {}: {}", session_id, e, exc_info=True)
            return JSONResponse({"error": "Failed to delete session"}, status_code=500)

    @app.put("/api/sessions/{session_id}/title")
    async def update_session_title(session_id: str, request: Request) -> JSONResponse:
        """Update the title of a chat session"""
        try:
            body = await request.json()
            new_title = body.get("title", "").strip()
            
            if not new_title:
                return JSONResponse({"error": "Title is required"}, status_code=400)
            
            # Validate title length (max 100 chars for database)
            if len(new_title) > 100:
                new_title = new_title[:100]
                logger.warning("Title truncated to 100 characters for session {}", session_id)
            
            # Verify session exists
            session = orchestrator.get_session(session_id)
            if not session:
                return JSONResponse({"error": "Session not found"}, status_code=404)
            
            # Update title in database via orchestrator
            success = orchestrator.update_session_title(session_id, new_title)
            
            if success:
                logger.info("Updated session title for {}: '{}'", session_id, new_title)
                return JSONResponse({
                    "ok": True,
                    "session_id": session_id,
                    "title": new_title
                })
            else:
                logger.error("Failed to update session title for {}", session_id)
                return JSONResponse({"error": "Failed to update session title"}, status_code=500)
            
        except Exception as e:
            logger.error("Failed to update session title for {}: {}", session_id, e, exc_info=True)
            return JSONResponse({"error": "Failed to update session title"}, status_code=500)
    
    @app.put("/api/sessions/{session_id}/pin")
    async def update_session_pin(session_id: str, request: Request) -> JSONResponse:
        """Update the pinned status of a chat session"""
        try:
            body = await request.json()
            pinned = body.get("pinned", False)
            pinned_order = body.get("pinned_order")
            
            # Ensure pinned is a boolean
            if not isinstance(pinned, bool):
                pinned = bool(pinned)
            
            # Verify session exists
            session = orchestrator.get_session(session_id)
            if not session:
                return JSONResponse({"error": "Session not found"}, status_code=404)
            
            # If pinning, calculate pinned_order if not provided
            if pinned and pinned_order is None:
                # Get max pinned_order and add 1
                all_sessions = orchestrator.get_all_sessions('active')
                max_order = 0
                for s in all_sessions:
                    s_pinned = getattr(s, 'pinned', False)
                    if isinstance(s_pinned, int):
                        s_pinned = bool(s_pinned)
                    if s_pinned:
                        s_order = getattr(s, 'pinned_order', 0)
                        if isinstance(s_order, int) and s_order > max_order:
                            max_order = s_order
                pinned_order = max_order + 1
            elif not pinned:
                # When unpinning, clear pinned_order to 0
                pinned_order = 0
            
            # Update pinned status in database via orchestrator
            success = orchestrator.update_session_pinned(session_id, pinned, pinned_order)
            
            if success:
                logger.info("Updated session pinned status for {}: {}, order: {}", session_id, pinned, pinned_order)
                return JSONResponse({
                    "ok": True,
                    "session_id": session_id,
                    "pinned": pinned,
                    "pinned_order": pinned_order
                })
            else:
                logger.error("Failed to update session pinned status for {}", session_id)
                return JSONResponse({"error": "Failed to update session pinned status"}, status_code=500)
            
        except Exception as e:
            logger.error("Failed to update session pinned status for {}: {}", session_id, e, exc_info=True)
            return JSONResponse({"error": "Failed to update session pinned status"}, status_code=500)
    
    @app.put("/api/sessions/{session_id}/pinned-order")
    async def update_pinned_order(session_id: str, request: Request) -> JSONResponse:
        """Update the pinned order of a chat session"""
        try:
            body = await request.json()
            pinned_order = body.get("pinned_order")
            
            if pinned_order is None or not isinstance(pinned_order, int):
                return JSONResponse({"error": "pinned_order is required and must be an integer"}, status_code=400)
            
            # Verify session exists
            session = orchestrator.get_session(session_id)
            if not session:
                return JSONResponse({"error": "Session not found"}, status_code=404)
            
            # Update pinned order in database via orchestrator
            success = orchestrator.update_pinned_order(session_id, pinned_order)
            
            if success:
                logger.info("Updated session pinned order for {}: {}", session_id, pinned_order)
                return JSONResponse({
                    "ok": True,
                    "session_id": session_id,
                    "pinned_order": pinned_order
                })
            else:
                logger.error("Failed to update session pinned order for {}", session_id)
                return JSONResponse({"error": "Failed to update session pinned order"}, status_code=500)
            
        except Exception as e:
            logger.error("Failed to update session pinned order for {}: {}", session_id, e, exc_info=True)
            return JSONResponse({"error": "Failed to update session pinned order"}, status_code=500)

    @app.get("/activity")
    async def get_activity(limit: int = 200):
        try:
            return JSONResponse(activity[-int(limit) :])
        except Exception:
            return JSONResponse(activity[-200:])


    # Helpers: JSON safety and AG-UI event translation
    def _json_safe(value):
        try:
            json.dumps(value)
            return value
        except Exception:
            if isinstance(value, dict):
                return {str(k): _json_safe(v) for k, v in value.items()}
            if isinstance(value, (list, tuple, set)):
                return [_json_safe(v) for v in value]
            return str(value)


    # -----------------------------
    # AG-UI Adapter Endpoints (Phase 1)
    # -----------------------------
    @app.post("/agui/turn")
    async def agui_turn(req: Request) -> JSONResponse:
        """Start a turn for AG-UI clients. Fire-and-forget; stream via /agui/stream."""
        try:
            body = await req.json()
        except Exception:
            return JSONResponse({"error": "bad_request"}, status_code=400)

        text = (body.get("text") or "").strip()
        if not text:
            return JSONResponse({"error": "missing_text"}, status_code=400)

        # Extract user_files from request body
        user_files = body.get("user_files", [])
        if not isinstance(user_files, list):
            return JSONResponse({"error": "user_files must be a list"}, status_code=400)

        # Use the session_id from the request (frontend-generated)
        requested_session_id = body.get("session_id")
        if not requested_session_id:
            return JSONResponse({"error": "missing_session_id"}, status_code=400)
        
        # Require an existing backend session; do not accept client-generated IDs
        session_id = requested_session_id
        fastapi_session_id = int(requested_session_id)

        try:
            existing = orchestrator.get_session(session_id)
            if not existing:
                return JSONResponse({"error": "unknown_session_id"}, status_code=404)
            logger.info("Using existing database session: {}", session_id)
        except Exception as e:
            logger.warning("Failed to get database session: {}", e)
            return JSONResponse({"error": "session_lookup_failed"}, status_code=500)
        
        q = agui_session_queues.setdefault(fastapi_session_id, asyncio.Queue())

        # Create session-specific run counter
        def get_next_run_counter():
            current_count = session_run_counters.get(fastapi_session_id, 0)
            session_run_counters[fastapi_session_id] = current_count + 1
            return current_count
        
        # Get or create AGUIService for this session
        agui_service = agui_services.setdefault(fastapi_session_id, AGUIService())
        
        # Create captured events list (same pattern as CLI)
        captured_events = []
        
        def emit_and_capture(evt: Dict[str, Any]) -> None:
            try:
                # Capture the event for pipeline_events (same pattern as CLI)
                captured_events.append(evt)
                
                # Convert event if needed (handles internal events like HITL)
                agui_events = agui_service.convert_event(_json_safe(evt))
                
                # Emit each converted event
                for agui_evt in agui_events:
                    payload = f"data: {json.dumps(agui_evt)}\n\n"
                    q.put_nowait(payload)
            except Exception as e:
                logger.warning("AGUI emit failed: {}", e)
        
        # Use session-scoped emitter to maintain counters across turns (same pattern as CLI)
        emitter = agui_emitters.setdefault(fastapi_session_id, AGUIEventEmitter(emit_and_capture, get_next_run_counter))
        emitter._captured_events = captured_events

        hitl_wait_options = {
            "hitl": {
                "wait_for_approval": (
                    lambda gate_id, timeout_ms=300000: asyncio.wait_for(
                        _fresh_waiter_future(fastapi_session_id, str(gate_id)),
                        (timeout_ms or 300000) / 1000.0,
                    )
                )
            }
        }

        async def _run_turn():
            # Clear captured events for this turn (same pattern as CLI)
            captured_events.clear()

            try:
                assistant = agui_assistants.setdefault(
                    fastapi_session_id,
                    Assistant(cfg, project_dir=project_dir, emitter=emitter, agui_service=agui_service, session_id=session_id),
                )
                if fastapi_session_id not in initialized_assistants:
                    await assistant.initialize()
                    initialized_assistants.add(fastapi_session_id)

                await assistant.execute_assistant_agent(
                    user_input=text,
                    turn_options=hitl_wait_options,
                    file_paths=user_files,
                    original_filenames=[Path(f).name for f in user_files] if user_files else [],
                    upload_intent="session",
                    mode="fastapi"
                )

            except Exception as e:
                logger.error("Error during assistant turn: {}", e)
                logger.error("Traceback: {}", traceback.format_exc())
            finally:
                # allow queued callbacks to flush then mark done
                await asyncio.sleep(0)
                await q.put("event: done\n\n")

        # Start run in background
        asyncio.create_task(_run_turn())

        return JSONResponse({"ok": True, "session_id": requested_session_id}, status_code=202)

    @app.get("/agui/stream")
    async def agui_stream(session: int) -> StreamingResponse:
        """SSE stream for AG-UI clients. Connect per session id."""
        try:
            session_id = int(session)
        except Exception:
            return StreamingResponse(iter(["data: {\"type\": \"error\", \"message\": \"bad_session\"}\n\n"]), media_type="text/event-stream")

        q = agui_session_queues.setdefault(session_id, asyncio.Queue())

        async def _generator():
            # Session ID is managed client-side, no need to emit event
            while True:
                chunk = await q.get()
                yield chunk
                if chunk.startswith("event: done"):
                    break

        return StreamingResponse(_generator(), media_type="text/event-stream")

    # Phase 4: HITL approval endpoint
    @app.post("/agui/approve")
    async def agui_approve(req: Request) -> JSONResponse:
        try:
            body = await req.json()
            session_id = int(body.get("session_id"))
            gate_id = str(body.get("gate_id"))
            decision = str(body.get("decision") or "").lower() or "approve"
            data = body.get("data")
        except Exception as e:
            return JSONResponse({"error": "bad_request"}, status_code=400)

        fut = hitl_waiters.setdefault(session_id, {}).get(gate_id)
        if not fut or fut.done():
            return JSONResponse({"error": "not_found"}, status_code=404)
        
        # Use AGUIService to resolve the HITL gate
        agui_service = agui_services.setdefault(session_id, AGUIService())
        agui_service.resolve_hitl_gate(gate_id, decision, "user")
        

        try:
            fut.set_result({"decision": decision, "data": data})
        except Exception as e:
            return JSONResponse({"error": "failed"}, status_code=500)

        # also emit an event so UI can reflect immediately
        try:
            q = agui_session_queues.setdefault(session_id, asyncio.Queue())
            emitter = AGUIEventEmitter(lambda evt: asyncio.create_task(q.put(f"data: {json.dumps(evt)}\n\n")))
            emitter.hitl_result(gate_id, decision, "user", _json_safe(data))
            logger.info("agui_approve emitted hitl_result event")
        except Exception as e:
            logger.error("agui_approve error emitting event:", e)

        return JSONResponse({"ok": True})



    logger.info("FastAPI application created successfully")
    return app

