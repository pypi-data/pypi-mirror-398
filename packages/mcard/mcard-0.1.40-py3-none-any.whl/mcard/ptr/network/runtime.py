"""
Network Runtime for CLM Network IO Operations (Refactored).

Matches the TypeScript NetworkRuntime implementation organization.
"""

import asyncio
import json
import logging
import re
import time
from threading import Thread
from typing import Any, Dict, Optional, Set, Tuple
from urllib.parse import urlencode, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler

from mcard import MCard
from mcard.model.card import MCardFromData
from mcard.model.card_collection import CardCollection

# Import new modular components
from .security import NetworkSecurity
from .infrastructure import NetworkCache, RateLimiter
from .serialization import MCardSerialization
from .http_client import HttpClient
from ..core.runtime import RuntimeExecutor
from ..core.p2p_session import P2PChatSession
from ..core.signaling_server import run_server, signaling

logger = logging.getLogger(__name__)

class NetworkRuntime(RuntimeExecutor):
    """
    Network Runtime for handling declarative network operations.
    Delegates implementation details to helper classes (Security, HttpClient, etc.)
    """
    
    def __init__(self, collection: Optional[CardCollection] = None):
        super().__init__()
        self.collection = collection
        
        # Initialize helpers
        self.security = NetworkSecurity() # Loads from env by default
        self.cache = NetworkCache(collection)
        self.rate_limiter = RateLimiter()
        self.http_client = HttpClient(self.rate_limiter, self.cache, self.security)
        
        self._servers: Dict[str, Any] = {}
        self._sessions: Dict[str, P2PChatSession] = {}
        
    # ============ Variable Interpolation ============
    
    def _interpolate(self, text: str, context: Any) -> str:
        """Simple variable interpolation: ${key} or ${input.key}."""
        if not text or not isinstance(text, str):
            return text
        
        def replacer(match):
            path = match.group(1)
            keys = path.split(".")
            val = context
            for key in keys:
                if isinstance(val, dict) and key in val:
                    val = val[key]
                else:
                    return ""  # Not found
            return str(val)
        
        return re.sub(r"\$\{([^}]+)\}", replacer, text)
    
    def _interpolate_headers(
        self, headers: Dict[str, str], context: Any
    ) -> Dict[str, str]:
        """Interpolate variables in headers."""
        return {k: self._interpolate(v, context) for k, v in headers.items()}

    # ============ Execution Entry Point ============

    def execute(
        self,
        concrete_impl: Dict[str, Any],
        target: Any, # Allows target to be None or MCard
        context: Dict[str, Any]
    ) -> Any:
        """Execute network operation (sync wrapper for async operations)."""
        builtin = concrete_impl.get("builtin")
        config = concrete_impl.get("config", {})
        
        if not builtin:
            raise ValueError("NetworkRuntime requires 'builtin' to be defined in config.")
        
        # Run async operations in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if builtin == "http_request":
            return loop.run_until_complete(self._handle_http_request(config, context))
        elif builtin == "http_get":
            return loop.run_until_complete(self._handle_http_get(config, context))
        elif builtin == "http_post":
            return loop.run_until_complete(self._handle_http_post(config, context))
        elif builtin == "load_url":
            return loop.run_until_complete(self._handle_load_url(config, context))
        elif builtin == "mcard_send":
            return loop.run_until_complete(self._handle_mcard_send(config, context))
        elif builtin == "listen_http":
            return self._handle_listen_http(config, context)
        elif builtin == "mcard_sync":
            return loop.run_until_complete(self._handle_mcard_sync(config, context))
        elif builtin == "listen_sync":
            return self._handle_listen_sync(config, context)
        elif builtin == "mcard_read":
            return self._handle_mcard_read(config, context)
        elif builtin == "session_record":
            return self._handle_session_record(config, context)
        elif builtin == "signaling_server":
            return self._handle_signaling_server(config, context)
        elif builtin == "clm_orchestrator":
            return self._handle_clm_orchestrator(config, context)
        elif builtin in ("webrtc_connect", "webrtc_listen"):
            logger.warning(f"WebRTC builtin {builtin} mocked in Python runtime.")
            return {"success": True, "connection_id": f"mock_conn_{int(time.time())}", "mock": True}
        # Add other builtins (webrtc, etc.) as needed
        else:
            raise ValueError(f"Unknown network builtin: {builtin}")

    # ============ Handlers ============

    async def _handle_http_request(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        url = self._interpolate(config.get("url", ""), context)
        method = config.get("method", "GET")
        headers = self._interpolate_headers(config.get("headers", {}), context)
        
        body = config.get("body")
        if isinstance(body, str):
            body = self._interpolate(body, context)
        elif isinstance(body, dict):
            body = json.dumps(body)
            
        # Handle query params interpolation
        parsed_url = urlparse(url)
        query_params = config.get("query_params", {})
        if query_params:
            interpolated_params = {
                k: self._interpolate(str(v), context) 
                for k, v in query_params.items()
            }
            url = f"{url}{'&' if parsed_url.query else '?'}{urlencode(interpolated_params)}"

        return await self.http_client.request(url, method, headers, body, config)

    async def _handle_http_get(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        return await self._handle_http_request({**config, "method": "GET"}, context)

    async def _handle_http_post(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        params = {**config, "method": "POST"}
        if config.get("json"):
            headers = params.get("headers", {})
            headers["Content-Type"] = "application/json"
            params["headers"] = headers
            params["body"] = json.dumps(config["json"])
        return await self._handle_http_request(params, context)

    async def _handle_load_url(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # load_url is just a GET that returns content specifically
        # reusing http_request for consistency
        res = await self._handle_http_request({**config, "method": "GET", "response_type": "text"}, context)
        if res.get("success"):
            return {
                "url": config.get("url"),
                "content": res.get("body"),
                "status": res.get("status"),
                "headers": res.get("headers"),
                "mcard_hash": res.get("mcard_hash")
            }
        return {"success": False, "error": res.get("error")}

    async def _handle_mcard_send(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        if not self.collection:
            raise ValueError("MCard Send requires a CardCollection.")
        
        hash_val = self._interpolate(config.get("hash", ""), context)
        url = self._interpolate(config.get("url", ""), context)
        
        card = self.collection.get(hash_val)
        if not card:
            return {"success": False, "error": f"MCard not found: {hash_val}"}
        
        payload = MCardSerialization.serialize(card)
        
        return await self._handle_http_post({
            "url": url,
            "json": payload,
            "headers": config.get("headers", {}),
        }, context)

    async def _handle_mcard_sync(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle mcard_sync builtin with bidirectional support."""
        if not self.collection:
            raise ValueError("MCard Sync requires a CardCollection.")
        
        mode = self._interpolate(config.get("mode", "pull"), context)
        url = self._interpolate(config.get("url", ""), context).rstrip("/")
        
        # 1. Get local manifest
        local_cards = list(self.collection.get_all_mcards_raw())
        local_hashes = {c.hash for c in local_cards}
        
        # 2. Get remote manifest
        manifest_res = await self._handle_http_request({
            "url": f"{url}/manifest",
            "method": "GET",
        }, context)
        
        if not manifest_res.get("success", True):
            raise ValueError(f"Failed to fetch remote manifest: {manifest_res.get('error')}")
        
        remote_hashes: Set[str] = set(manifest_res.get("body", []))
        
        stats = {
            "mode": mode,
            "local_total": len(local_hashes),
            "remote_total": len(remote_hashes),
            "synced": 0,
        }
        
        async def push_cards() -> int:
            """Push local cards to remote."""
            to_send = [c for c in local_cards if c.hash not in remote_hashes]
            if not to_send:
                return 0
            
            payload = {"cards": [MCardSerialization.serialize(c) for c in to_send]}
            push_res = await self._handle_http_post({
                "url": f"{url}/batch",
                "json": payload,
                "headers": config.get("headers", {}),
            }, context)
            
            if not push_res.get("success", True):
                raise ValueError(f"Failed to push batch: {push_res.get('error')}")
            
            return len(to_send)
        
        async def pull_cards() -> int:
            """Pull remote cards to local."""
            needed = [h for h in remote_hashes if h not in local_hashes]
            if not needed:
                return 0
            
            fetch_res = await self._handle_http_post({
                "url": f"{url}/get",
                "json": {"hashes": needed},
                "headers": config.get("headers", {}),
            }, context)
            
            if not fetch_res.get("success", True):
                raise ValueError(f"Failed to pull batch: {fetch_res.get('error')}")
            
            received = fetch_res.get("body", {}).get("cards", [])
            for card_json in received:
                card = MCardSerialization.deserialize(card_json)
                self.collection.add(card)
            
            return len(received)
        
        if mode == "push":
            stats["synced"] = await push_cards()
        elif mode == "pull":
            stats["synced"] = await pull_cards()
        elif mode in ("both", "bidirectional"):
            pushed = await push_cards()
            pulled = await pull_cards()
            stats["pushed"] = pushed
            stats["pulled"] = pulled
            stats["synced"] = pushed + pulled
        else:
            raise ValueError(f"Unknown sync mode: {mode}. Valid: push, pull, both")
        
        return {"success": True, "stats": stats}

    def _handle_listen_http(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        port = int(self._interpolate(str(config.get("port", 3000)), context))
        path_endpoint = self._interpolate(config.get("path", "/mcard"), context)
        
        # Need to capture self for use in handler (since HTTPServer creates instances)
        runtime = self 
        
        class MCardHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == path_endpoint:
                    try:
                        content_length = int(self.headers.get("Content-Length", 0))
                        body = self.rfile.read(content_length)
                        payload = json.loads(body.decode("utf-8"))
                        
                        card = MCardSerialization.deserialize(payload)
                        
                        if runtime.collection:
                            runtime.collection.add(card)
                        
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": True,
                            "hash": card.hash
                        }).encode())
                    except Exception as e:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": str(e)
                        }).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                logger.debug(f"[Network] {args[0]}")
        
        server = HTTPServer(("", port), MCardHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        logger.info(f"[Network] Listening on port {port} at {path_endpoint}")
        self._servers[f"http_{port}"] = server
        
        return {
            "success": True,
            "message": f"Server started on port {port}",
            "port": port,
            "path": path_endpoint,
        }

    def _handle_listen_sync(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
         # Placeholder for listen_sync implementation mirroring JS logic
         # Logic would be similar to listen_http but handling /manifest, /batch, /get routes
         # For brevity in this refactor, returning not implemented or strict minimal
         logger.warning("listen_sync not fully ported in this refactoring step")
         return {"success": False, "error": "Not implemented"}

    
    def _handle_mcard_read(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle reading an MCard from the collection."""
        if not self.collection:
            raise ValueError("MCard Read requires a CardCollection.")
            
        hash_val = self._interpolate(config.get("hash", ""), context)
        parse_json = config.get("parse_json", False)
        
        card = self.collection.get(hash_val)
        if not card:
            return {"success": False, "error": f"MCard not found: {hash_val}"}
            
        content = card.get_content()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
            
        result = {
            "success": True,
            "hash": card.hash,
            "content": content,
        }
        
        if parse_json:
            try:
                result["json"] = json.loads(content)
            except json.JSONDecodeError:
                result["error"] = "Failed to parse JSON content"
                # Keep success true as we did read the card? 
                # Or maybe fail? The JS implementation might return partial.
                # Let's include raw content still.
        
        return result

    def _handle_session_record(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle incremental session recording.
        Supports single operations and batch mode.
        """
        if not self.collection:
            raise ValueError("Session Record requires a CardCollection.")

        # Support aliases
        action = config.get("action") or config.get("operation") or "record"
        action = self._interpolate(action, context)
        
        session_id = config.get("session_id") or config.get("sessionId") or ""
        session_id = self._interpolate(session_id, context)
        
        # Helper to get/create session
        def get_session(sid, cfg):
            if not sid:
                return None
            if sid not in self._sessions:
                init_head = cfg.get("initial_head_hash")
                max_buffer_val = cfg.get("maxBufferSize", 5)
                max_buffer = int(self._interpolate(str(max_buffer_val), context))
                self._sessions[sid] = P2PChatSession(
                    self.collection, 
                    sid, 
                    max_buffer_size=max_buffer,
                    initial_head_hash=init_head
                )
            return self._sessions[sid]

        if action == "batch":
            operations = config.get("operations", [])
            last_result = {"success": True}
            
            for op_config in operations:
                # Merge parent session_id if not present
                if not op_config.get("session_id") and not op_config.get("sessionId"):
                    op_config["session_id"] = session_id
                
                # Recursive call
                last_result = self._handle_session_record(op_config, context)
                if not last_result.get("success"):
                    return last_result
            
            return last_result

        if not session_id:
            return {"success": False, "error": "Missing session_id"}
            
        if action == "init":
            # Explicit initialization
            get_session(session_id, config)
            return {"success": True, "session_id": session_id}

        session = get_session(session_id, config)
        
        if action in ("record", "add"):
            sender = self._interpolate(config.get("sender", "unknown"), context)
            message = self._interpolate(config.get("content") or config.get("message", ""), context)
            
            # Add message
            checkpoint_hash = session.add_message(sender, message)
            
            return {
                "success": True,
                "checkpoint_hash": checkpoint_hash, # None if not flushed
                "head_hash": session.get_head_hash()
            }
            
        elif action in ("checkpoint", "flush"):
            checkpoint_hash = session.checkpoint()
            return {
                "success": True,
                "checkpoint_hash": checkpoint_hash,
                "head_hash": checkpoint_hash
            }
            
        elif action == "summarize":
            summary_hash = session.summarize(keep_originals=config.get("keep_originals", False))
            return {
                "success": True,
                "summary_hash": summary_hash
            }
            
        else:
            return {"success": False, "error": f"Unknown session action: {action}"}

    def _handle_signaling_server(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle signaling server operations."""
        action = self._interpolate(config.get("action", "start"), context)
        
        if action == "start":
            port = int(self._interpolate(str(config.get("port", 3000)), context))
            try:
                # Use global signaling instance implicit in run_server
                server = run_server(port, background=True)
                actual_port = getattr(server, 'actual_port', port)
                
                self._servers[f"signaling_{actual_port}"] = server
                
                return {
                    "success": True,
                    "port": actual_port,
                    "message": f"Signaling server started on port {actual_port}"
                }
            except Exception as e:
                logger.error(f"Failed to start signaling server: {e}")
                return {"success": False, "error": str(e)}
                
        elif action == "stop":
            port = int(self._interpolate(str(config.get("port", 3000)), context))
            server_key = f"signaling_{port}"
            
            if server_key in self._servers:
                server = self._servers[server_key]
                server.shutdown()
                del self._servers[server_key]
                return {"success": True, "message": "Server stopped"}
            else:
                return {"success": False, "error": "Server not found"}
                
    def _handle_clm_orchestrator(self, config: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle multi-agent orchestration.
        Executes a sequence of steps (CLMs, background processes, servers).
        """
        import subprocess
        import sys
        import os
        from mcard.ptr.runner import CLMRunner
        
        steps = config.get("steps", [])
        results = {}
        state = {**context} if isinstance(context, dict) else {}
        
        started_processes = {}
        started_server_ids = set()
        
        # Helper for path resolution
        def resolve_path(fname):
            if "pcard_dir" in state and not os.path.isabs(fname):
                 return os.path.join(state["pcard_dir"], fname)
            return fname
        
        try:
            for step in steps:
                action = step.get("action")
                name = step.get("name", action)
                logger.info(f"[Orchestrator] Running step: {name}")
                
                if action == "run_clm":
                    check_file = step.get("file")
                    file_path = resolve_path(check_file)
                    
                    if not os.path.exists(file_path):
                         raise FileNotFoundError(f"File not found: {file_path}")

                    step_input = step.get("input", {})
                    interpolated_input = {k: self._interpolate(str(v), state) for k, v in step_input.items()}
                    
                    # Update pcard_dir for the sub-run
                    next_pcard_dir = os.path.dirname(os.path.abspath(file_path))
                    combined_ctx = {
                        **state, 
                        **interpolated_input,
                        "pcard_dir": next_pcard_dir
                    }
                    
                    runner = CLMRunner()
                    try:
                        report = runner.run_file(file_path, context=combined_ctx)
                        results[name] = report
                        
                        if report.get("status") != "success":
                            if not step.get("continue_on_error", False):
                                raise RuntimeError(f"Step {name} failed: {report.get('result')}")
                    except Exception as e:
                         if not step.get("continue_on_error", False):
                             raise e
                         logger.error(f"Step {name} failed with exception: {e}")
                    
                elif action == "run_clm_background":
                    check_file = step.get("file")
                    file_path = resolve_path(check_file)
                    id_key = step.get("id_key", "pid")
                    
                    if not os.path.exists(file_path):
                         # Warn but maybe let CLI fail? No, better fail fast.
                         logger.warning(f"[Orchestrator] Background file not found: {file_path}")
                    
                    step_input = step.get("input", {})
                    interpolated_input = {k: self._interpolate(str(v), state) for k, v in step_input.items()}
                    input_json = json.dumps(interpolated_input)
                    
                    env_vars = step.get("env", {})
                    proc_env = os.environ.copy()
                    for k, v in env_vars.items():
                        proc_env[k] = self._interpolate(str(v), state)

                    cmd = [sys.executable, "-m", "mcard.ptr.cli", "run", file_path, "--context", input_json]
                    
                    db_path = step.get("db") or step.get("db_path")
                    if db_path:
                         # CLI --db arg
                         cmd.extend(["--db", resolve_path(db_path)])

                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=proc_env)
                    started_processes[id_key] = proc
                    state[id_key] = proc.pid
                    logger.info(f"Started background process {file_path} (PID: {proc.pid})")
                    
                elif action == "start_signaling_server":
                    port = step.get("port", 3000)
                    id_key = step.get("id_key", "server_id")
                    
                    res = self._handle_signaling_server({
                        "action": "start",
                        "port": port
                    }, state)
                    
                    if not res.get("success"):
                        raise RuntimeError(f"Failed to start signaling server: {res.get('error')}")
                        
                    state[id_key] = f"signaling_{res.get('port')}"
                    started_server_ids.add(id_key)
                    
                elif action == "stop_signaling_server":
                    id_key = step.get("id_key")
                    val = state.get(id_key)
                    if val and val.startswith("signaling_"):
                        port = int(val.split("_")[1])
                        self._handle_signaling_server({
                            "action": "stop",
                            "port": port
                        }, state)
                        if id_key in started_server_ids:
                            started_server_ids.remove(id_key)
                        
                elif action == "stop_process":
                    pid_key = step.get("pid_key")
                    pid = state.get(pid_key)
                    
                    if pid:
                         try:
                             os.kill(int(pid), 15) # SIGTERM
                             logger.info(f"Killed process {pid}")
                         except Exception as e:
                             logger.warning(f"Failed to kill process {pid}: {e}")
                             
                    if pid_key in started_processes:
                        del started_processes[pid_key]

                wait_ms = step.get("wait_after", 0)
                if wait_ms > 0:
                    time.sleep(wait_ms / 1000.0)

        finally:
            for pid_key, proc in list(started_processes.items()):
                if proc.poll() is None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=1)
                    except Exception:
                        try:
                            proc.kill()
                        except:
                            pass
                    logger.info(f"[Orchestrator] Auto-cleaned background process {proc.pid}")
            
            for server_key in list(started_server_ids):
                val = state.get(server_key)
                if val and val.startswith("signaling_"):
                     try:
                        port = int(val.split("_")[1])
                        self._handle_signaling_server({"action": "stop", "port": port}, state)
                        logger.info(f"[Orchestrator] Auto-stopped signaling server on {port}")
                     except Exception as e:
                         logger.error(f"[Orchestrator] Failed to auto-stop server: {e}")
             
        return {"success": True, "results": results}

    def validate_environment(self) -> bool:
        """Check if runtime environment (aiohttp) is available."""
        from .http_client import AIOHTTP_AVAILABLE
        return AIOHTTP_AVAILABLE
