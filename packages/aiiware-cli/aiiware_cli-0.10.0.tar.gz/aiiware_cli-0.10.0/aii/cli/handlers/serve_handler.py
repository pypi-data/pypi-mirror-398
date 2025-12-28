# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Serve command handler for AII CLI (v0.6.0).

Handles API server management:
- serve / serve start (start API server)
- serve stop (stop running server)
- serve status (check server status)
- serve restart (restart server)
"""


from typing import Any

from ...cli.command_router import CommandRoute


async def handle_serve_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """
    Handle 'serve' command - manage API server.

    Args:
        route: CommandRoute with command/subcommand/args
        config_manager: ConfigManager instance
        output_config: OutputConfig instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = route.args
    subcommand = args.get("serve_subcommand")

    # Route to appropriate handler
    if subcommand == "stop":
        return await _handle_serve_stop(args)
    elif subcommand == "status":
        return await _handle_serve_status(config_manager)
    elif subcommand == "restart":
        return await _handle_serve_restart(args, config_manager)
    else:
        # Default: start server (backwards compatible with `aii serve`)
        return await _handle_serve_start(args)


async def _handle_serve_start(args: dict) -> int:
    """Handle 'serve start' or 'serve' (start server)."""
    host = args.get("host", "127.0.0.1")
    port = args.get("port", 16169)
    api_keys = args.get("api_keys") or []
    verbose = args.get("verbose", False) or args.get("debug", False)
    daemon = args.get("daemon", False)

    if daemon:
        # Daemon mode: Start server as background process
        import subprocess
        import sys
        from pathlib import Path

        # Build command to run server in foreground (daemon process will detach)
        cmd = [
            sys.executable, "-m", "aii.cli.serve",
            "--host", host,
            "--port", str(port),
        ]

        # Add API keys if provided
        for key in api_keys:
            cmd.extend(["--api-key", key])

        if verbose:
            cmd.append("--verbose")

        # Start as daemon (detached process)
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from terminal
            )

            # Save PID for management
            pid_file = Path.home() / ".aii" / "server.pid"
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            pid_file.write_text(str(process.pid))

            print(f"🚀 Aii Server started in daemon mode")
            print(f"   PID: {process.pid}")
            print(f"   Host: {host}")
            print(f"   Port: {port}")
            print(f"   Status: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/api/status")
            print(f"\nTo stop: aii serve stop")
            return 0

        except Exception as e:
            print(f"❌ Failed to start daemon: {e}")
            return 1

    else:
        # Foreground mode: Run server directly
        from aii.cli.serve import start_api_server

        try:
            await start_api_server(host, port, api_keys, verbose)
            return 0
        except KeyboardInterrupt:
            # Graceful shutdown already handled
            return 0
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            import traceback
            traceback.print_exc()
            return 1


async def _handle_serve_stop(args: dict) -> int:
    """Handle 'serve stop' (stop server)."""
    from pathlib import Path
    import os
    import signal
    import time

    pid_file = Path.home() / ".aii" / "server.pid"
    force = args.get("force", False)

    # Check if PID file exists
    if not pid_file.exists():
        print("❌ No server PID file found")
        print("   Server may not be running, or was started manually")
        return 1

    # Read PID
    try:
        pid = int(pid_file.read_text().strip())
    except ValueError:
        print("❌ Invalid PID file")
        pid_file.unlink()
        return 1

    # Check if process exists
    try:
        os.kill(pid, 0)  # Signal 0 = check existence
    except OSError:
        print(f"⚠️  Process {pid} not found (server may have crashed)")
        pid_file.unlink()
        return 1

    # Stop server
    try:
        if force:
            print(f"🛑 Force stopping server (PID {pid})...")
            os.kill(pid, signal.SIGKILL)
            pid_file.unlink()
            print("✅ Server force-stopped")
            return 0
        else:
            print(f"🛑 Stopping server (PID {pid})...")
            os.kill(pid, signal.SIGTERM)

            # Wait for graceful shutdown (max 5 seconds)
            for i in range(50):
                try:
                    os.kill(pid, 0)  # Check if still running
                    time.sleep(0.1)
                except OSError:
                    # Process exited
                    pid_file.unlink()
                    print("✅ Server stopped")
                    return 0

            # Still running after 5s, force kill
            print("⚠️  Server didn't stop gracefully, force stopping...")
            os.kill(pid, signal.SIGKILL)
            pid_file.unlink()
            print("✅ Server stopped")
            return 0

    except Exception as e:
        print(f"❌ Failed to stop server: {e}")
        return 1


async def _handle_serve_status(config_manager: Any) -> int:
    """Handle 'serve status' (check server status)."""
    from pathlib import Path
    import os
    import httpx

    pid_file = Path.home() / ".aii" / "server.pid"
    host = config_manager.get("api.host", "127.0.0.1")
    port = config_manager.get("api.port", 16169)

    # Check PID file
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Check if process exists
            try:
                os.kill(pid, 0)
                pid_status = f"✅ Running (PID: {pid})"
            except OSError:
                pid_status = "❌ Not running (stale PID file)"
                pid_file.unlink()
        except ValueError:
            pid_status = "❌ Invalid PID file"
            pid_file.unlink()
    else:
        pid_status = "❌ Not running (no PID file)"

    # Check HTTP health endpoint
    try:
        # Use 127.0.0.1 instead of localhost to avoid proxy issues
        check_host = "127.0.0.1" if host == "localhost" else host
        response = httpx.get(
            f"http://{check_host}:{port}/api/status",
            timeout=1.0
        )
        if response.status_code == 200:
            health_status = "✅ Healthy"
            data = response.json()
            uptime = data.get("uptime", 0)
            version = data.get("version", "unknown")
        else:
            health_status = f"⚠️  HTTP {response.status_code}"
            uptime = 0
            version = "unknown"
    except (httpx.ConnectError, httpx.TimeoutException):
        health_status = "❌ Not responding"
        uptime = 0
        version = "unknown"

    # Display status
    print("\n📊 Aii Server Status")
    print("=" * 50)
    print(f"Process:  {pid_status}")
    print(f"Health:   {health_status}")
    print(f"Address:  http://{host}:{port}")
    if uptime > 0:
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        print(f"Uptime:   {hours}h {minutes}m {seconds}s")
        print(f"Version:  {version}")
    print("=" * 50)
    print()

    # Return exit code based on health
    if "✅" in health_status:
        return 0
    else:
        return 1


async def _handle_serve_restart(args: dict, config_manager: Any) -> int:
    """Handle 'serve restart' (restart server)."""
    print("🔄 Restarting server...")

    # Stop server
    stop_result = await _handle_serve_stop({"force": False})
    if stop_result != 0:
        print("⚠️  Failed to stop server, attempting to start anyway...")

    # Wait a moment for port to be released
    import asyncio
    await asyncio.sleep(1)

    # Start server in daemon mode
    print("🚀 Starting server...")
    start_args = {
        "host": config_manager.get("api.host", "127.0.0.1"),
        "port": config_manager.get("api.port", 16169),
        "api_keys": config_manager.get("api.keys", []),
        "daemon": True,
        "verbose": False
    }

    start_result = await _handle_serve_start(start_args)
    if start_result == 0:
        print("✅ Server restarted successfully")
    else:
        print("❌ Failed to restart server")

    return start_result
