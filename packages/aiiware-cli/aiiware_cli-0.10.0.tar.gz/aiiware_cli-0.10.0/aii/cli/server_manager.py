# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Server lifecycle management for AII CLI.

Features:
- Detect if server is running (port 16169 health check)
- Start server as background process
- Monitor server health
- Gracefully shutdown server
- Clean up orphaned processes
- PID file tracking (~/.aii/server.pid)
"""


import os
import subprocess
import httpx
import signal
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ServerManager:
    """Manage Aii Server lifecycle"""

    PID_FILE = Path.home() / ".aii" / "server.pid"

    def __init__(self, config):
        """
        Initialize ServerManager.

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.port = config.get("api.port", 16169)
        self.host = config.get("api.host", "127.0.0.1")

    def is_server_running(self) -> bool:
        """
        Check if server is responding on port.

        Returns:
            bool: True if server is healthy and responding
        """
        try:
            url = f"http://{self.host}:{self.port}/health"
            logger.debug(f"Checking server health: {url}")
            # Use 127.0.0.1 instead of localhost to avoid proxy issues
            if self.host == "localhost":
                url = f"http://127.0.0.1:{self.port}/health"

            # Disable proxy for localhost health checks to avoid system proxy interference
            # trust_env=False prevents httpx from using system/environment proxy settings
            with httpx.Client(trust_env=False) as client:
                response = client.get(url, timeout=0.5)
                is_running = response.status_code == 200
                logger.debug(f"Server health check result: {is_running}")
                return is_running
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as e:
            logger.debug(f"Server health check failed: {e}")
            return False

    async def start_server(self, background: bool = True) -> bool:
        """
        Start Aii server as subprocess.

        Args:
            background: If True, start as daemon process

        Returns:
            True if server started successfully
        """
        # Build command
        cmd = [
            "aii", "serve",
            "--port", str(self.port),
            "--host", self.host,
        ]

        if background:
            cmd.append("--daemon")

        # Start process
        try:
            if background:
                # Detach from parent process (daemon)
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True  # Detach from terminal
                )

                # Save PID
                self.write_pid(process.pid)

                logger.info(f"Server started with PID {process.pid}")
                return True
            else:
                # Foreground (for manual `aii serve`)
                subprocess.run(cmd)
                return True

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def stop_server(self, force: bool = False) -> bool:
        """
        Stop running server.

        Args:
            force: If True, use SIGKILL instead of SIGTERM

        Returns:
            True if server stopped successfully
        """
        pid = self.read_pid()
        if not pid:
            logger.warning("No server PID found")
            return False

        try:
            if force:
                os.kill(pid, signal.SIGKILL)
                logger.info(f"Force-killed server (PID {pid})")
            else:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to server (PID {pid})")

            # Wait for process to exit
            for i in range(50):  # 5 seconds
                if not self.is_process_running(pid):
                    self.cleanup_stale_pid()
                    logger.info(f"Server stopped (PID {pid})")
                    return True
                time.sleep(0.1)

            # Process didn't exit, force kill
            logger.warning(f"Server didn't exit gracefully, force killing (PID {pid})")
            os.kill(pid, signal.SIGKILL)
            self.cleanup_stale_pid()
            return True

        except ProcessLookupError:
            logger.info(f"Process not found (PID {pid}), cleaning up stale PID")
            self.cleanup_stale_pid()
            return False

    def restart_server(self) -> bool:
        """
        Restart server (stop then start).

        Returns:
            True if restart successful
        """
        logger.info("Restarting server...")

        # Stop server
        if self.read_pid():
            self.stop_server()

        # Wait a moment for port to be released
        time.sleep(0.5)

        # Start server
        import asyncio
        return asyncio.run(self.start_server(background=True))

    def write_pid(self, pid: int):
        """
        Write server PID to file.

        Args:
            pid: Process ID to write
        """
        self.PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.PID_FILE.write_text(str(pid))
        logger.debug(f"Wrote PID {pid} to {self.PID_FILE}")

    def read_pid(self) -> Optional[int]:
        """
        Read server PID from file.

        Returns:
            Process ID if file exists and valid, None otherwise
        """
        if self.PID_FILE.exists():
            try:
                pid = int(self.PID_FILE.read_text().strip())
                logger.debug(f"Read PID {pid} from {self.PID_FILE}")
                return pid
            except ValueError:
                logger.warning(f"Invalid PID in {self.PID_FILE}")
                return None
        return None

    def is_process_running(self, pid: int) -> bool:
        """
        Check if process exists.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running
        """
        try:
            os.kill(pid, 0)  # Signal 0 = check existence
            return True
        except OSError:
            return False

    def cleanup_stale_pid(self):
        """Remove PID file if process not running"""
        if self.PID_FILE.exists():
            self.PID_FILE.unlink()
            logger.debug(f"Removed stale PID file {self.PID_FILE}")

    def get_server_status(self) -> dict:
        """
        Get detailed server status.

        Returns:
            dict: Server status information
        """
        pid = self.read_pid()
        running = self.is_server_running()

        return {
            "running": running,
            "pid": pid if pid and self.is_process_running(pid) else None,
            "port": self.port,
            "host": self.host,
            "health_endpoint": f"http://{self.host}:{self.port}/health"
        }
