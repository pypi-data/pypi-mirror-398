"""
Unified GodotWebLauncher with mode-based API.

Modes:
  - local-dev  : interactive local dev (opens system browser)
  - local-train: headless Playwright (local automated runs)
  - hf-demo    : HF Spaces inference / demo (serve only; no browser)
  - hf-train   : HF Spaces training (serve only; no browser)

Place in: utdg_env/launcher/godot_launcher.py
"""

from __future__ import annotations

import os
import time
import logging
import subprocess
import shutil
import socket
import platform
import threading
import webbrowser
import http.server
from pathlib import Path
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# -------------------------
# COI HTTP Handler
# -------------------------
class COIHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that sets Cross-Origin Isolation headers required by SharedArrayBuffer."""

    def end_headers(self):
        # Required headers for SharedArrayBuffer and Godot
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")

        # Cache control to avoid stale builds during development
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

        super().end_headers()

    def log_message(self, format, *args):
        # Lower noise by using the module logger
        logger.debug("%s - %s", self.address_string(), format % args)


# -------------------------
# Utility functions
# -------------------------
def _is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _find_available_port(start_port: int = 8080, max_attempts: int = 50, host: str = "127.0.0.1") -> int:
    for p in range(start_port, start_port + max_attempts):
        if _is_port_available(p, host=host):
            return p
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts - 1}")


# -------------------------
# Launcher
# -------------------------
class GodotWebLauncher:
    """
    Mode-based Godot web launcher.

    Use `GodotWebLauncher.from_mode(mode, **kwargs)` to construct.

    Public methods:
      - launch() -> (url, port)
      - stop()
      - __enter__/__exit__ for context manager
    """

    VALID_MODES = {"local-dev", "local-train", "hf-demo", "hf-train"}

    def __init__(
        self,
        build_dir: str = "builds/web",
        http_port: int = 8080,
        ws_host: str = "localhost",
        ws_port: int = 8000,
        headless: bool = False,
        auto_port: bool = True,
        open_browser: bool = False,
        playwright_args: Optional[dict] = None,
        mode: Optional[str] = None,
    ):
        self.build_dir = Path(build_dir)
        self.http_port = int(http_port)
        self.ws_host = ws_host
        self.ws_port = int(ws_port)
        self.headless = bool(headless)
        self.auto_port = bool(auto_port)
        self.open_browser = bool(open_browser)
        self.playwright_args = playwright_args or {}
        self.mode = mode or "custom"

        # server state (subprocess-based for no GIL contention)
        self._http_server_process: Optional[subprocess.Popen] = None
        self._server_script_path: Optional[str] = None

        # playwright state (only used when headless=True)
        self._playwright = None
        self._browser = None
        self._browser_context = None
        self._browser_page = None

        # Validate build directory exists
        if not self.build_dir.exists():
            raise FileNotFoundError(f"Godot build directory not found: {self.build_dir}")

    # -------------------------
    # Factory: from_mode
    # -------------------------
    @classmethod
    def from_mode(cls, mode: str, **kwargs) -> "GodotWebLauncher":
        """
        Construct launcher from predefined mode.

        Modes:
          - local-dev:  interactive local (opens system browser)
          - local-train: headless Playwright (local automated training)
          - hf-demo:    HF Spaces demo (serve only)
          - hf-train:   HF Spaces training (serve only)
        """
        mode = str(mode)
        if mode not in cls.VALID_MODES:
            raise ValueError(f"Unknown mode '{mode}'. Valid: {sorted(cls.VALID_MODES)}")

        # sensible defaults per mode
        params = {
            "build_dir": kwargs.get("build_dir", "builds/web"),
            "http_port": kwargs.get("http_port", 8080),
            "ws_host": kwargs.get("ws_host", "localhost"),
            "ws_port": kwargs.get("ws_port", 8000),
            "auto_port": kwargs.get("auto_port", True),
            "playwright_args": kwargs.get("playwright_args", None),
            "mode": mode,
        }

        if mode == "local-dev":
            params.update({"headless": False, "open_browser": True})
        elif mode == "local-train":
            params.update({"headless": True, "open_browser": False})
        elif mode in ("hf-demo", "hf-train"):
            # On HF Spaces the page is delivered by the Space frontend iframe;
            # do not attempt to open local system browser or Playwright.
            params.update({"headless": False, "open_browser": False})
        else:
            # fallback: keep kwargs
            params.update({"headless": kwargs.get("headless", False), "open_browser": kwargs.get("open_browser", False)})

        # allow overrides
        for k, v in kwargs.items():
            params[k] = v

        return cls(**params)

    # -------------------------
    # HTTP server lifecycle
    # -------------------------
    # -------------------------
    # HTTP server lifecycle
    # -------------------------
    def start_http_server(self) -> Tuple[str, int]:
        """Start HTTP server in background subprocess and return (url, port)."""
        if self.auto_port and not _is_port_available(self.http_port):
            logger.warning("Port %d in use, searching for alternative...", self.http_port)
            self.http_port = _find_available_port(self.http_port)

        # Create server script that runs in separate process (avoids GIL contention)
        server_script = f'''
import http.server
import socketserver
from pathlib import Path

class COIHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that adds Cross-Origin Isolation headers for Godot WebAssembly."""

    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        # Add Cross-Origin Isolation headers required by Godot WebAssembly
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")

        # Prevent Browser Refresh
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')

        super().end_headers()

    def log_message(self, format, *args):
        # Suppress request logs to keep output clean
        pass

if __name__ == "__main__":
    PORT = {self.http_port}
    DIRECTORY = r"{self.build_dir}"

    from functools import partial
    Handler = partial(COIHTTPRequestHandler, directory=DIRECTORY)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving with COI headers at http://localhost:{{PORT}}", flush=True)
        httpd.serve_forever()
'''

        # Write server script to temporary file
        import tempfile
        import sys
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(server_script)
            self._server_script_path = f.name

        # Start HTTP server in separate process (no GIL contention!)
        self._http_server_process = subprocess.Popen(
            [sys.executable, self._server_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for server to start
        time.sleep(1.0)

        # Check if server started successfully
        if self._http_server_process.poll() is not None:
            stderr = self._http_server_process.stderr.read() if self._http_server_process.stderr else ""
            raise RuntimeError(f"HTTP server failed to start: {stderr}")

        logger.info("Started HTTP server at http://localhost:%d serving %s (mode=%s)", self.http_port, self.build_dir, self.mode)

        return f"http://localhost:{self.http_port}", self.http_port

    # -------------------------
    # Browser launching
    # -------------------------
    def _launch_system_browser(self, url: str) -> None:
        logger.info("Opening system browser to %s", url)
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.exception("Failed to open system browser: %s", e)

    def _launch_playwright(self, url: str) -> None:
        # Playwright is optional and only imported if needed
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            raise RuntimeError("Playwright is required for headless mode. Install with:\n"
                               "pip install playwright && playwright install chromium") from e

        logger.info(f"Starting Playwright Chromium (headless={self.headless})...")
        self._playwright = sync_playwright().start()

        chromium = self._playwright.chromium

        # Base args
        args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--enable-features=SharedArrayBuffer",
        ]

        # Add WebGL fix flags ONLY if running headless (where they are needed)
        if self.headless:
            args.extend([
                "--ignore-gpu-blocklist",
                "--use-gl=angle",
                "--use-gl=swiftshader", # Fallback
            ])

        pw_args = {
            "headless": self.headless,
            "args": args,
        }
        pw_args.update(self.playwright_args or {})

        self._browser = chromium.launch(**pw_args)
        self._browser_context = self._browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 720})
        self._browser_page = self._browser_context.new_page()

        # Capture console messages from the page (helpful for debugging)
        def _on_console(msg):
            try:
                if msg.type == "error":
                    logger.error("[Godot][browser] %s", msg.text)
                else:
                    logger.debug("[Godot][browser] %s", msg.text)
            except Exception:
                logger.exception("Error handling Playwright console message")

        self._browser_page.on("console", _on_console)

        logger.info("Navigating to %s (waiting for canvas)...", url)
        try:
            self._browser_page.goto(url, wait_until="networkidle", timeout=30000)
            # Wait for Godot canvas to appear (best-effort)
            self._browser_page.wait_for_selector("canvas", timeout=30000)
            logger.info("Chromium loaded Godot page successfully.")
        except Exception as e:
            logger.warning("Page may not be fully loaded or canvas not found: %s", e)

    # -------------------------
    # Public API: launch / stop
    # -------------------------
    # ------------------------------------------------------------
    # Public API: launch / stop
    # ------------------------------------------------------------
    def launch(self) -> Tuple[str, int]:
        """
        Start server (and optionally browser). Returns (http_url, port).
        """
        http_url, port = self.start_http_server()

        # Behavior per mode:
        if self.mode == "local-train":
            # local-train = Playwright automation (headless or visible)
            logger.info(f"Mode is {self.mode}: Launching Playwright (headless={self.headless}).")
            self._launch_playwright(http_url)
        elif self.mode == "local-dev":
            if self.open_browser:
                logger.info("Opening system browser (interactive mode).")
                self._launch_system_browser(http_url)
        else:
            # hf-train / hf-demo (no launcher action needed)
            logger.info("Not opening browser locally (mode=%s).", self.mode)

        # Print human-friendly instructions (helpful when running interactively)
        print(self.get_instructions(http_url))
        return http_url, port

    def stop(self) -> None:
        """Cleanly stop server and browser (if used)."""
        # Stop Playwright browser
        if self._browser_page:
            try:
                self._browser_page.close()
            except Exception:
                pass
            self._browser_page = None

        if self._browser_context:
            try:
                self._browser_context.close()
            except Exception:
                pass
            self._browser_context = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        # Stop HTTP server subprocess
        if self._http_server_process:
            logger.info("Stopping HTTP server subprocess...")
            self._http_server_process.terminate()
            try:
                self._http_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("HTTP server didn't stop gracefully, killing...")
                self._http_server_process.kill()
            self._http_server_process = None
            logger.info("✓ HTTP server stopped")

        # Clean up temporary server script
        if self._server_script_path:
            try:
                import os
                os.unlink(self._server_script_path)
                self._server_script_path = None
            except Exception as e:
                logger.warning("Failed to clean up server script: %s", e)

        logger.info("GodotWebLauncher stopped (mode=%s).", self.mode)

    # -------------------------
    # Utilities
    # -------------------------
    def get_instructions(self, http_url: str) -> str:
        """Return a short instruction banner depending on mode."""
        ws_url = f"ws://{self.ws_host}:{self.ws_port}"
        base = f"""
╔══════════════════════════════════════════════════════════════╗
║          Godot Web Build ({self.mode})                       ║
╚══════════════════════════════════════════════════════════════╝

🌐 Godot Web Build:  {http_url}
🔌 WebSocket Server: {ws_url}

"""
        if self.mode == "local-dev":
            base += "🚀 System browser should open automatically (interactive).\n\n"
        elif self.mode == "local-train":
            base += "🤖 Running headless via Playwright (local training). No browser window will appear.\n\n"
        elif self.mode in ("hf-demo", "hf-train"):
            base += "📡 HF Spaces mode — the Space frontend should load this URL inside its iframe. No browser launched from container.\n\n"

        base += "⚠️ IMPORTANT: Configure your Godot game to connect to the WebSocket server at:\n"
        base += f"   {ws_url}\n\n"
        base += "Press Ctrl+C to stop.\n"
        base += "═══════════════════════════════════════════════════════════════\n"
        return base

    # -------------------------
    # Context manager
    # -------------------------
    def __enter__(self) -> "GodotWebLauncher":
        self.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


# -------------------------
# Native Launcher
# -------------------------
class GodotNativeLauncher:
    """
    Launcher for native Godot builds (desktop).
    Supports launching the binary directly or via macOS .app bundle.
    """

    def __init__(
        self,
        godot_path: str,
        headless: bool = False,
    ):
        self.godot_path = Path(godot_path)
        self.headless = headless
        self.process: Optional[subprocess.Popen] = None

    def launch(self) -> None:
        """Launch the native Godot application."""
        executable = self._resolve_executable_path(self.godot_path)

        args = [str(executable)]
        if self.headless:
            args.append("--headless")

        logger.info(f"[GodotNativeLauncher] Launching: {' '.join(args)}")

        try:
            # Popen allows the process to run in background
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL if self.headless else None,
                stderr=subprocess.PIPE,  # Capture stderr to log errors
            )
            logger.info(f"[GodotNativeLauncher] Process started (PID: {self.process.pid})")

            # Give Godot time to initialize and start WebSocket server
            logger.info("[GodotNativeLauncher] Waiting 2s for Godot to initialize...")
            time.sleep(2.0)
        except Exception as e:
            logger.error(f"[GodotNativeLauncher] Failed to launch: {e}")
            raise

    def stop(self) -> None:
        """Terminate the Godot application."""
        if self.process:
            logger.info("[GodotNativeLauncher] Terminating process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                logger.warning("[GodotNativeLauncher] Force killing process...")
                self.process.kill()
            self.process = None

    def _resolve_executable_path(self, path: Path) -> Path:
        """
        Resolve the actual binary path.
        - If path is a file, return it.
        - If path is a macOS .app bundle, find the binary inside Contents/MacOS.
        """
        if not path.exists():
            raise FileNotFoundError(f"[GodotNativeLauncher] Path not found: {path}")

        if path.suffix == ".app" and path.is_dir() and platform.system() == "Darwin":
            # It's a macOS app bundle. Look for the binary inside.
            macos_dir = path / "Contents" / "MacOS"
            if macos_dir.exists():
                # Usually the binary has the same name as the .app (minus extension)
                # But sometimes it's different. We pick the first executable file found.
                for child in macos_dir.iterdir():
                    if child.is_file() and os.access(child, os.X_OK):
                        return child

            # Fallback: try `open -n -a`? No, Popen needs a binary.
            raise RuntimeError(f"[GodotNativeLauncher] Could not find executable in macOS bundle: {path}")

        if path.is_file():
            return path

        raise RuntimeError(f"[GodotNativeLauncher] Path is not a file or valid .app bundle: {path}")

    def __enter__(self) -> "GodotNativeLauncher":
        self.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


# -------------------------
# Convenience top-level helper
# -------------------------
def create_launcher(mode: str = "local-dev", **kwargs) -> GodotWebLauncher:
    """
    Convenience wrapper: GodotWebLauncher.from_mode(mode, **kwargs)
    """
    return GodotWebLauncher.from_mode(mode, **kwargs)


# -------------------------
# Simple CLI for manual runs
# -------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Godot Web Build Launcher (unified)")
    parser.add_argument("--mode", default="local-dev", choices=list(GodotWebLauncher.VALID_MODES))
    parser.add_argument("--build-dir", default="builds/web")
    parser.add_argument("--http-port", type=int, default=8080)
    parser.add_argument("--ws-host", default="localhost")
    parser.add_argument("--ws-port", type=int, default=8000)
    parser.add_argument("--no-auto-port", dest="auto_port", action="store_false")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    launcher = GodotWebLauncher.from_mode(
        args.mode,
        build_dir=args.build_dir,
        http_port=args.http_port,
        ws_host=args.ws_host,
        ws_port=args.ws_port,
        auto_port=args.auto_port,
    )
    try:
        url, port = launcher.launch()
        print(f"Serving at: {url}")
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        launcher.stop()
