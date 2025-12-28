#!/usr/bin/env python3
"""
wgctl - WireGuard CLI Wrapper Tool

A command-line tool for unified WireGuard connection management.

Usage:
    wgctl <interface> <action> [--json]

Actions:
    connect     - Establish connection (reads config if present)
    disconnect  - Terminate connection
    reconnect   - Re-establish connection
    status      - Check connection status
    list        - Show all available interfaces
    request     - Request tunnel (with automatic expiration)
    cron        - Check leases, auto-connect, health checks
    test        - Run tunnel tests (Ping/TCP)
"""

__version__ = "0.6.1"

import argparse
import json
import socket
import subprocess
import sys
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path

import yaml


class ExitCode(IntEnum):
    """Exit codes for wgctl."""

    SUCCESS = 0
    ERROR = 1
    CONFIG_NOT_FOUND = 2
    PERMISSION_ERROR = 3

WIREGUARD_CONFIG_DIR = Path("/etc/wireguard")
LEASE_DIR = Path("/run/wgctl")
CONFIG_DIR = Path("/etc/wgctl")
DEFAULT_TTL_SECONDS = 60  # 1 minute


def run_command(cmd: list[str]) -> tuple[bool, str, str]:
    """Execute a command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        return False, "", f"Command not found: {cmd[0]}"
    except PermissionError:
        return False, "", "Permission denied"


def config_exists(interface: str) -> bool:
    """Check if the WireGuard config exists."""
    config_path = WIREGUARD_CONFIG_DIR / f"{interface}.conf"
    return config_path.exists()


def get_config_path(interface: str) -> Path:
    """Return the path to the wgctl config file."""
    return CONFIG_DIR / f"{interface}.yaml"


def read_config(interface: str) -> dict | None:
    """Read the YAML config for an interface."""
    config_path = get_config_path(interface)
    if not config_path.exists():
        return None
    try:
        with config_path.open() as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None


def get_lease_path(interface: str) -> Path:
    """Return the path to the lease file."""
    return LEASE_DIR / f"{interface}.lease"


def read_lease(interface: str) -> dict | None:
    """Read the lease file for an interface."""
    lease_path = get_lease_path(interface)
    if not lease_path.exists():
        return None
    try:
        with lease_path.open() as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def write_lease(
    interface: str,
    expires_at: float,
    test_ping: str | None = None,
    test_tcp: tuple[str, int] | None = None,
    on_test_fail: str = "ignore",
) -> bool:
    """Write the lease file for an interface."""
    try:
        LEASE_DIR.mkdir(parents=True, exist_ok=True)
        lease_path = get_lease_path(interface)
        lease_data: dict = {
            "interface": interface,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if test_ping:
            lease_data["test_ping"] = test_ping
        if test_tcp:
            lease_data["test_tcp"] = {"host": test_tcp[0], "port": test_tcp[1]}
        if test_ping or test_tcp:
            lease_data["on_test_fail"] = on_test_fail
        with lease_path.open("w") as f:
            json.dump(lease_data, f)
        return True
    except OSError:
        return False


def delete_lease(interface: str) -> bool:
    """Delete the lease file for an interface."""
    lease_path = get_lease_path(interface)
    try:
        if lease_path.exists():
            lease_path.unlink()
        return True
    except OSError:
        return False


def is_connected(interface: str) -> bool:
    """Check if the WireGuard interface is active."""
    success, _, _ = run_command(["wg", "show", interface])
    return success


def test_ping(host: str, timeout: int = 2) -> bool:
    """Run a ping test to the host."""
    success, _, _ = run_command(["ping", "-c", "1", "-W", str(timeout), host])
    return success


def test_tcp(host: str, port: int, timeout: int = 2) -> bool:
    """Run a TCP connect test to host:port."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, OSError):
        return False


def is_tunnel_working(interface: str, lease: dict) -> bool:
    """Check if interface is active and all configured tests pass."""
    if not is_connected(interface):
        return False

    # Ping test
    ping_host = lease.get("test_ping")
    if ping_host and not test_ping(ping_host):
        return False

    # TCP test
    tcp_test = lease.get("test_tcp")
    if tcp_test and not test_tcp(tcp_test["host"], tcp_test["port"]):
        return False

    return True


def parse_wg_show(output: str) -> dict:
    """Parse the output of 'wg show <interface>' for peer details."""
    details = {}
    current_section = "interface"

    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("peer:"):
            current_section = "peer"
            details["public_key"] = line.split(":", 1)[1].strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()

            if current_section == "peer":
                if key == "endpoint":
                    details["endpoint"] = value
                elif key == "allowed_ips":
                    details["allowed_ips"] = value
                elif key == "latest_handshake":
                    details["latest_handshake"] = value
                elif key == "transfer":
                    # Format: "1.24 GiB received, 256.3 MiB sent"
                    parts = value.split(",")
                    if len(parts) == 2:
                        details["transfer_rx"] = parts[0].replace("received", "").strip()
                        details["transfer_tx"] = parts[1].replace("sent", "").strip()

    return details


def wg_up(interface: str) -> tuple[bool, str]:
    """Wrapper for wg-quick up."""
    success, _, stderr = run_command(["wg-quick", "up", interface])
    return success, stderr


def wg_down(interface: str) -> tuple[bool, str]:
    """Wrapper for wg-quick down."""
    success, _, stderr = run_command(["wg-quick", "down", interface])
    return success, stderr


def do_connect(
    interface: str,
    test_ping_host: str | None = None,
    test_tcp_target: tuple[str, int] | None = None,
    on_test_fail: str = "ignore",
) -> dict:
    """Establish connection (permanent, without expiration)."""
    # Config as fallback for missing CLI parameters
    if not test_ping_host and not test_tcp_target:
        config = read_config(interface)
        if config:
            test_ping_host = config.get("test_ping")
            tcp = config.get("test_tcp")
            if tcp:
                test_tcp_target = (tcp["host"], tcp["port"])
            on_test_fail = config.get("on_test_fail", on_test_fail)

    if not config_exists(interface):
        return {
            "status": "error",
            "message": f"Config not found: {interface}.conf",
            "exit_code": ExitCode.CONFIG_NOT_FOUND,
        }

    if is_connected(interface):
        # Already connected - set lease to permanent
        write_lease(interface, 0, test_ping_host, test_tcp_target, on_test_fail)
        return {"status": "success", "exit_code": ExitCode.SUCCESS}

    success, stderr = wg_up(interface)
    if success:
        # Lease with expires_at=0 for "permanent"
        write_lease(interface, 0, test_ping_host, test_tcp_target, on_test_fail)
        return {"status": "success", "exit_code": ExitCode.SUCCESS}

    if "Permission denied" in stderr or "Operation not permitted" in stderr:
        return {
            "status": "error",
            "message": "Permission denied",
            "exit_code": ExitCode.PERMISSION_ERROR,
        }

    return {
        "status": "error",
        "message": stderr.strip() or "Unknown error",
        "exit_code": ExitCode.ERROR,
    }


def do_disconnect(interface: str) -> dict:
    """Terminate connection."""
    if not is_connected(interface):
        # Not connected - delete lease anyway
        delete_lease(interface)
        result: dict = {"status": "success", "exit_code": ExitCode.SUCCESS}
    else:
        success, stderr = wg_down(interface)
        if success:
            delete_lease(interface)
            result = {"status": "success", "exit_code": ExitCode.SUCCESS}
        elif "Permission denied" in stderr or "Operation not permitted" in stderr:
            return {
                "status": "error",
                "message": "Permission denied",
                "exit_code": ExitCode.PERMISSION_ERROR,
            }
        else:
            return {
                "status": "error",
                "message": stderr.strip() or "Unknown error",
                "exit_code": ExitCode.ERROR,
            }

    # Warning if auto_connect is enabled
    config = read_config(interface)
    if config and config.get("auto_connect", False):
        result["warning"] = "auto_connect is enabled, will reconnect on next cron"

    return result


def do_reconnect(interface: str) -> dict:
    """Re-establish connection (disconnect + connect)."""
    disconnect_result = do_disconnect(interface)
    if disconnect_result.get("exit_code") != ExitCode.SUCCESS:
        return disconnect_result
    return do_connect(interface)


def do_status(interface: str) -> dict:
    """Check connection status (read-only, does not run tests)."""
    result: dict = {"exit_code": ExitCode.SUCCESS}

    # Read lease information
    lease = read_lease(interface)
    if lease:
        expires_at = lease.get("expires_at", 0)
        if expires_at == 0:
            result["lease"] = {"mode": "permanent"}
        else:
            now = datetime.now(timezone.utc).timestamp()
            remaining = expires_at - now
            result["lease"] = {
                "mode": "temporary",
                "expires_at": datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
                "remaining_seconds": int(remaining) if remaining > 0 else 0,
                "expired": remaining <= 0,
            }
        # Show configured tests (without running them)
        if lease.get("test_ping"):
            result["lease"]["test_ping"] = lease["test_ping"]
        if lease.get("test_tcp"):
            result["lease"]["test_tcp"] = lease["test_tcp"]
        if lease.get("on_test_fail"):
            result["lease"]["on_test_fail"] = lease["on_test_fail"]

    if not is_connected(interface):
        result["status"] = "disconnected"
        return result

    # Get details via wg show
    success, stdout, stderr = run_command(["wg", "show", interface])
    if not success:
        if "Permission denied" in stderr or "Operation not permitted" in stderr:
            result["status"] = "error"
            result["message"] = "Permission denied"
            result["exit_code"] = ExitCode.PERMISSION_ERROR
            return result
        result["status"] = "error"
        result["message"] = stderr.strip() or "Unknown error"
        result["exit_code"] = ExitCode.ERROR
        return result

    details = parse_wg_show(stdout)
    result["status"] = "connected"
    result["details"] = details
    return result


def do_request(
    interface: str,
    ttl: int = DEFAULT_TTL_SECONDS,
    test_ping_host: str | None = None,
    test_tcp_target: tuple[str, int] | None = None,
    on_test_fail: str = "ignore",
) -> dict:
    """Request a tunnel and set the expiration time."""
    if not config_exists(interface):
        return {
            "status": "error",
            "message": f"Config not found: {interface}.conf",
            "exit_code": ExitCode.CONFIG_NOT_FOUND,
        }

    # Check if interface has permanent lease
    lease = read_lease(interface)
    if lease and lease.get("expires_at", 0) == 0:
        return {
            "status": "error",
            "message": "Interface has permanent lease, use disconnect first",
            "exit_code": ExitCode.ERROR,
        }

    # Check if config has auto_connect enabled
    config = read_config(interface)
    if config and config.get("auto_connect", False):
        return {
            "status": "error",
            "message": "Interface has auto_connect enabled, use connect instead",
            "exit_code": ExitCode.ERROR,
        }

    # Calculate expiration time
    expires_at = datetime.now(timezone.utc).timestamp() + ttl

    # Connect if not connected
    if not is_connected(interface):
        success, stderr = wg_up(interface)
        if not success:
            if "Permission denied" in stderr or "Operation not permitted" in stderr:
                return {
                    "status": "error",
                    "message": "Permission denied",
                    "exit_code": ExitCode.PERMISSION_ERROR,
                }
            return {
                "status": "error",
                "message": stderr.strip() or "Unknown error",
                "exit_code": ExitCode.ERROR,
            }

    # Write/update lease
    if not write_lease(interface, expires_at, test_ping_host, test_tcp_target, on_test_fail):
        return {
            "status": "error",
            "message": "Failed to write lease file",
            "exit_code": ExitCode.ERROR,
        }

    return {
        "status": "success",
        "expires_at": datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
        "ttl": ttl,
        "exit_code": ExitCode.SUCCESS,
    }


def handle_test_failure(
    interface: str, lease: dict, remaining: int | None = None
) -> dict:
    """Handle failed tests based on on_test_fail setting."""
    action = lease.get("on_test_fail", "ignore")

    if action == "ignore":
        result: dict = {"interface": interface, "status": "test_failed"}
        if remaining is not None:
            result["remaining_seconds"] = remaining
        return result

    elif action == "disconnect":
        if is_connected(interface):
            wg_down(interface)
        delete_lease(interface)
        return {"interface": interface, "status": "disconnected"}

    else:  # reconnect
        if is_connected(interface):
            wg_down(interface)
        success, stderr = wg_up(interface)
        if success:
            result = {"interface": interface, "status": "reconnected"}
        else:
            result = {
                "interface": interface,
                "status": "error",
                "message": stderr.strip() or "Failed to reconnect",
            }
        if remaining is not None:
            result["remaining_seconds"] = remaining
        return result


def do_cron() -> dict:
    """Check all leases, run auto-connect, and perform health checks."""
    results = []
    now = datetime.now(timezone.utc).timestamp()
    processed_interfaces: set[str] = set()

    # 1. Process all lease files
    if LEASE_DIR.exists():
        for lease_file in LEASE_DIR.glob("*.lease"):
            interface = lease_file.stem
            processed_interfaces.add(interface)
            lease = read_lease(interface)

            if lease is None:
                continue

            expires_at = lease.get("expires_at", 0)
            has_tests = lease.get("test_ping") or lease.get("test_tcp")

            # expires_at == 0 means "permanent" (manually connected)
            if expires_at == 0:
                # Check permanent leases with tests
                if has_tests:
                    if is_tunnel_working(interface, lease):
                        results.append({
                            "interface": interface,
                            "status": "permanent",
                        })
                    else:
                        results.append(handle_test_failure(interface, lease))
                else:
                    results.append({
                        "interface": interface,
                        "status": "permanent",
                    })
                continue

            if now > expires_at:
                # Lease expired - close tunnel
                if is_connected(interface):
                    success, stderr = wg_down(interface)
                    if not success:
                        results.append({
                            "interface": interface,
                            "status": "error",
                            "message": stderr.strip() or "Failed to disconnect",
                        })
                        continue

                # Delete lease file
                delete_lease(interface)

                results.append({
                    "interface": interface,
                    "status": "expired",
                })
            else:
                # Lease still valid - check if tunnel is working
                remaining = int(expires_at - now)

                if is_tunnel_working(interface, lease):
                    results.append({
                        "interface": interface,
                        "status": "active",
                        "remaining_seconds": remaining,
                    })
                else:
                    results.append(handle_test_failure(interface, lease, remaining))

    # 2. Auto-connect for configs without active lease
    if CONFIG_DIR.exists():
        for config_file in CONFIG_DIR.glob("*.yaml"):
            interface = config_file.stem

            # Skip if already processed above
            if interface in processed_interfaces:
                continue

            config = read_config(interface)
            if config is None or not config.get("auto_connect", False):
                continue

            # WireGuard config must exist
            if not config_exists(interface):
                results.append({
                    "interface": interface,
                    "status": "error",
                    "message": f"Config not found: {interface}.conf",
                })
                continue

            # Test parameters from config
            test_ping = config.get("test_ping")
            tcp = config.get("test_tcp")
            test_tcp = (tcp["host"], tcp["port"]) if tcp else None
            on_fail = config.get("on_test_fail", "ignore")

            if not is_connected(interface):
                success, stderr = wg_up(interface)
                if success:
                    write_lease(interface, 0, test_ping, test_tcp, on_fail)
                    results.append({
                        "interface": interface,
                        "status": "auto_connected",
                    })
                else:
                    results.append({
                        "interface": interface,
                        "status": "error",
                        "message": stderr.strip() or "Failed to connect",
                    })
            else:
                # Already connected (e.g., externally), create lease
                write_lease(interface, 0, test_ping, test_tcp, on_fail)
                results.append({
                    "interface": interface,
                    "status": "auto_connected",
                })

    return {
        "status": "success",
        "results": results,
        "exit_code": ExitCode.SUCCESS,
    }


def do_test(
    interface: str,
    test_ping_host: str | None = None,
    test_tcp_target: tuple[str, int] | None = None,
) -> dict:
    """Run tunnel tests (from lease or via CLI parameters)."""
    # First check if interface is connected
    if not is_connected(interface):
        return {
            "status": "error",
            "message": "Interface not connected",
            "exit_code": ExitCode.ERROR,
        }

    # Read tests from lease if no CLI parameters
    lease = read_lease(interface)
    use_fallback = not test_ping_host and not test_tcp_target

    if use_fallback:
        if lease:
            test_ping_host = lease.get("test_ping")
            tcp_test = lease.get("test_tcp")
            if tcp_test:
                test_tcp_target = (tcp_test["host"], tcp_test["port"])

        # Config as second fallback
        if not test_ping_host and not test_tcp_target:
            config = read_config(interface)
            if config:
                test_ping_host = config.get("test_ping")
                tcp = config.get("test_tcp")
                if tcp:
                    test_tcp_target = (tcp["host"], tcp["port"])

    # No tests configured?
    if not test_ping_host and not test_tcp_target:
        return {
            "status": "error",
            "message": "No tests configured (use --test-ping or --test-tcp, or configure in lease/config)",
            "exit_code": ExitCode.ERROR,
        }

    results: dict = {"tests": []}

    # Ping test
    if test_ping_host:
        ping_ok = test_ping(test_ping_host)
        results["tests"].append({
            "type": "ping",
            "host": test_ping_host,
            "success": ping_ok,
        })

    # TCP test
    if test_tcp_target:
        tcp_ok = test_tcp(test_tcp_target[0], test_tcp_target[1])
        results["tests"].append({
            "type": "tcp",
            "host": test_tcp_target[0],
            "port": test_tcp_target[1],
            "success": tcp_ok,
        })

    # Overall result
    all_passed = all(t["success"] for t in results["tests"])
    results["status"] = "success" if all_passed else "failed"
    results["exit_code"] = ExitCode.SUCCESS if all_passed else ExitCode.ERROR

    return results


def do_list() -> dict:
    """List all available WireGuard interfaces."""
    interfaces = []

    # Configs from /etc/wireguard
    if WIREGUARD_CONFIG_DIR.exists():
        for config_file in WIREGUARD_CONFIG_DIR.glob("*.conf"):
            name = config_file.stem
            connected = is_connected(name)

            info: dict = {
                "name": name,
                "status": "connected" if connected else "disconnected",
            }

            # Lease info
            lease = read_lease(name)
            if lease:
                expires_at = lease.get("expires_at", 0)
                info["lease"] = "permanent" if expires_at == 0 else "temporary"

            # Config info
            config = read_config(name)
            if config and config.get("auto_connect", False):
                info["auto_connect"] = True

            interfaces.append(info)

    return {
        "status": "success",
        "interfaces": interfaces,
        "exit_code": ExitCode.SUCCESS,
    }


def do_doctor() -> dict:
    """Check dependencies and show versions."""
    import shutil
    import platform

    deps: list = []

    # wgctl version
    deps.append({"name": "wgctl", "version": __version__, "path": None, "ok": True})

    # Python version
    deps.append({
        "name": "python",
        "version": platform.python_version(),
        "path": sys.executable,
        "ok": True,
    })

    # wg-quick
    wg_quick_path = shutil.which("wg-quick")
    if wg_quick_path:
        deps.append({"name": "wg-quick", "version": None, "path": wg_quick_path, "ok": True})
    else:
        deps.append({"name": "wg-quick", "version": None, "path": None, "ok": False})

    # wg
    wg_path = shutil.which("wg")
    if wg_path:
        # Try to get version
        try:
            result = subprocess.run(
                ["wg", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            version = None
        deps.append({"name": "wg", "version": version, "path": wg_path, "ok": True})
    else:
        deps.append({"name": "wg", "version": None, "path": None, "ok": False})

    # Check if all OK
    all_ok = all(d["ok"] for d in deps)

    return {
        "status": "success" if all_ok else "error",
        "dependencies": deps,
        "exit_code": ExitCode.SUCCESS if all_ok else ExitCode.ERROR,
    }


def output(result: dict, action: str, interface: str | None, json_mode: bool) -> None:
    """Unified output (text or JSON)."""
    exit_code = result.pop("exit_code", ExitCode.SUCCESS)

    if json_mode:
        result["action"] = action
        if interface:
            result["interface"] = interface
        print(json.dumps(result))
    else:
        if action == "doctor":
            deps = result.get("dependencies", [])
            for dep in deps:
                status = "OK" if dep["ok"] else "MISSING"
                version = dep["version"] or ""
                path = f"({dep['path']})" if dep["path"] else ""
                print(f"{dep['name']}: {version}{path} [{status}]")
        elif action == "list":
            interfaces = result.get("interfaces", [])
            if not interfaces:
                print("No interfaces found")
            else:
                for iface in interfaces:
                    parts = [iface["status"]]
                    if "lease" in iface:
                        parts.append(iface["lease"])
                    if iface.get("auto_connect"):
                        parts.append("auto_connect")
                    extras = f" ({', '.join(parts[1:])})" if len(parts) > 1 else ""
                    print(f"{iface['name']}: {parts[0]}{extras}")
        else:
            status = result.get("status", "error")
            if status == "error":
                message = result.get("message", "Unknown error")
                print(f"error: {message}")
            else:
                print(status)
                # Print warning if present
                if "warning" in result:
                    print(f"warning: {result['warning']}")

    sys.exit(exit_code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WireGuard CLI Wrapper Tool",
        prog="wgctl",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "interface",
        nargs="?",
        help="Name of the WireGuard interface (e.g., wg0), not required for 'list'",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["connect", "disconnect", "reconnect", "status", "list", "request", "cron", "test", "doctor"],
        help="Action to execute",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_mode",
        help="Output in JSON format",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=DEFAULT_TTL_SECONDS,
        help=f"Lease duration in seconds for 'request' (default: {DEFAULT_TTL_SECONDS})",
    )
    parser.add_argument(
        "--test-ping",
        dest="test_ping",
        metavar="HOST",
        help="Host for ping test with 'request', 'connect', or 'test'",
    )
    parser.add_argument(
        "--test-tcp",
        dest="test_tcp",
        nargs=2,
        metavar=("HOST", "PORT"),
        help="Host and port for TCP test with 'request', 'connect', or 'test'",
    )
    parser.add_argument(
        "--on-test-fail",
        dest="on_test_fail",
        choices=["ignore", "reconnect", "disconnect"],
        default="ignore",
        help="Behavior on failed test (default: ignore)",
    )
    args = parser.parse_args()

    # "list", "cron", "doctor" can be first or second argument
    no_interface_actions = ("list", "cron", "doctor")
    if args.interface in no_interface_actions:
        args.action = args.interface
        args.interface = None
    elif args.action in no_interface_actions:
        args.interface = None

    # Validation
    if args.action is None:
        parser.error("action is required")
    if args.action not in ("list", "cron", "doctor") and args.interface is None:
        parser.error("interface is required for this action")

    # Port validation for --test-tcp
    test_tcp_tuple = None
    if args.test_tcp:
        try:
            port = int(args.test_tcp[1])
        except ValueError:
            parser.error(f"Invalid port: {args.test_tcp[1]} (must be a number)")
        if not 1 <= port <= 65535:
            parser.error(f"Invalid port: {port} (must be 1-65535)")
        test_tcp_tuple = (args.test_tcp[0], port)

    # Execute action
    if args.action == "list":
        result = do_list()
        output(result, "list", None, args.json_mode)
    elif args.action == "request":
        assert args.interface is not None
        result = do_request(
            args.interface, args.ttl, args.test_ping, test_tcp_tuple, args.on_test_fail
        )
        output(result, args.action, args.interface, args.json_mode)
    elif args.action == "cron":
        result = do_cron()
        output(result, args.action, None, args.json_mode)
    elif args.action == "doctor":
        result = do_doctor()
        output(result, args.action, None, args.json_mode)
    elif args.action == "test":
        assert args.interface is not None
        result = do_test(args.interface, args.test_ping, test_tcp_tuple)
        output(result, args.action, args.interface, args.json_mode)
    elif args.action == "connect":
        assert args.interface is not None
        result = do_connect(
            args.interface, args.test_ping, test_tcp_tuple, args.on_test_fail
        )
        output(result, args.action, args.interface, args.json_mode)
    else:
        assert args.interface is not None
        actions = {
            "disconnect": do_disconnect,
            "reconnect": do_reconnect,
            "status": do_status,
        }
        result = actions[args.action](args.interface)
        output(result, args.action, args.interface, args.json_mode)


if __name__ == "__main__":
    main()
