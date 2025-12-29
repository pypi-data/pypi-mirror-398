"""Core port detection and process management."""

from dataclasses import dataclass
from enum import Enum
import os
import platform
import re
import signal
import subprocess
import psutil


class ProcessType(Enum):
    """Known dev server/process types."""

    NODE = "node"
    PYTHON = "python"
    JAVA = "java"
    RUBY = "ruby"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    DOTNET = "dotnet"
    OTHER = "other"


# Common dev server port ranges
DEV_PORT_RANGES = [
    (3000, 3999),  # React, Next.js, Rails, etc.
    (4000, 4999),  # Phoenix, Gatsby, etc.
    (5000, 5999),  # Flask, Vite, etc.
    (6000, 6999),  # X11, various dev tools
    (8000, 8999),  # Django, uvicorn, Spring Boot, etc.
    (9000, 9999),  # PHP, SonarQube, etc.
]

# Process name patterns to identify dev server types
PROCESS_PATTERNS: dict[str, ProcessType] = {
    "node": ProcessType.NODE,
    "npm": ProcessType.NODE,
    "npx": ProcessType.NODE,
    "bun": ProcessType.NODE,
    "deno": ProcessType.NODE,
    "python": ProcessType.PYTHON,
    "python3": ProcessType.PYTHON,
    "uvicorn": ProcessType.PYTHON,
    "gunicorn": ProcessType.PYTHON,
    "flask": ProcessType.PYTHON,
    "java": ProcessType.JAVA,
    "ruby": ProcessType.RUBY,
    "rails": ProcessType.RUBY,
    "go": ProcessType.GO,
    "cargo": ProcessType.RUST,
    "rustc": ProcessType.RUST,
    "php": ProcessType.PHP,
    "dotnet": ProcessType.DOTNET,
}

# Command patterns to identify specific frameworks
FRAMEWORK_PATTERNS: dict[str, str] = {
    "next": "Next.js",
    "vite": "Vite",
    "webpack": "Webpack",
    "react-scripts": "Create React App",
    "vue-cli-service": "Vue CLI",
    "angular": "Angular",
    "nuxt": "Nuxt",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "astro": "Astro",
    "svelte": "SvelteKit",
    "flask": "Flask",
    "django": "Django",
    "uvicorn": "Uvicorn",
    "gunicorn": "Gunicorn",
    "fastapi": "FastAPI",
    "spring": "Spring Boot",
    "rails": "Rails",
    "phoenix": "Phoenix",
    "hugo": "Hugo",
    "jekyll": "Jekyll",
    "firebase": "Firebase",
    "emulator": "Emulator",
}


@dataclass
class PortInfo:
    """Information about a process listening on a port."""

    port: int
    pid: int
    name: str
    cmdline: str
    process_type: ProcessType
    framework: str | None
    memory_mb: float
    cpu_percent: float
    user: str
    create_time: float

    @property
    def short_cmd(self) -> str:
        """Get a shortened version of the command line."""
        if len(self.cmdline) <= 50:
            return self.cmdline
        return self.cmdline[:47] + "..."

    @property
    def display_name(self) -> str:
        """Get a friendly display name for the process."""
        if self.framework:
            return self.framework
        return self.name


def is_dev_port(port: int) -> bool:
    """Check if a port is in common dev server ranges."""
    return any(start <= port <= end for start, end in DEV_PORT_RANGES)


def identify_process_type(name: str) -> ProcessType:
    """Identify the process type from the process name."""
    name_lower = name.lower()
    for pattern, proc_type in PROCESS_PATTERNS.items():
        if pattern in name_lower:
            return proc_type
    return ProcessType.OTHER


def identify_framework(cmdline: str) -> str | None:
    """Try to identify the framework from the command line."""
    cmdline_lower = cmdline.lower()
    for pattern, framework in FRAMEWORK_PATTERNS.items():
        if pattern in cmdline_lower:
            return framework
    return None


def _get_process_info(pid: int) -> dict | None:
    """Get detailed process info using psutil."""
    try:
        proc = psutil.Process(pid)
        cmdline_parts = proc.cmdline()
        cmdline = " ".join(cmdline_parts) if cmdline_parts else proc.name()

        with proc.oneshot():
            memory_info = proc.memory_info()
            return {
                "name": proc.name(),
                "cmdline": cmdline,
                "memory_mb": memory_info.rss / (1024 * 1024),
                "cpu_percent": proc.cpu_percent(),
                "user": proc.username(),
                "create_time": proc.create_time(),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None


def _get_listening_ports_lsof() -> dict[int, int]:
    """Get listening ports using lsof (works on macOS/Linux without root)."""
    ports_to_pids: dict[int, int] = {}

    try:
        # lsof -iTCP -sTCP:LISTEN -P -n gives us listening TCP ports
        result = subprocess.run(
            ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        for line in result.stdout.strip().split("\n")[1:]:  # Skip header
            if not line:
                continue

            parts = line.split()
            if len(parts) < 9:
                continue

            # Format: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
            try:
                pid = int(parts[1])
                name_part = parts[8]  # e.g., "*:3000" or "127.0.0.1:8000"

                # Extract port from name (format: addr:port or *:port)
                if ":" in name_part:
                    port_str = name_part.split(":")[-1]
                    # Handle cases like "3000->127.0.0.1:3001"
                    port_str = port_str.split("->")[0]
                    port = int(port_str)
                    ports_to_pids[port] = pid
            except (ValueError, IndexError):
                continue

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return ports_to_pids


def _get_listening_ports_ss() -> dict[int, int]:
    """Get listening ports using ss (Linux alternative)."""
    ports_to_pids: dict[int, int] = {}

    try:
        # ss -tlnp gives listening TCP ports with process info
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        pid_pattern = re.compile(r'pid=(\d+)')

        for line in result.stdout.strip().split("\n")[1:]:  # Skip header
            if not line:
                continue

            parts = line.split()
            if len(parts) < 5:
                continue

            try:
                # Local address is typically in column 4
                local_addr = parts[3]
                if ":" in local_addr:
                    port = int(local_addr.rsplit(":", 1)[-1])

                    # Find PID in the users column
                    pid_match = pid_pattern.search(line)
                    if pid_match:
                        pid = int(pid_match.group(1))
                        ports_to_pids[port] = pid
            except (ValueError, IndexError):
                continue

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return ports_to_pids


def _get_listening_ports_netstat() -> dict[int, int]:
    """Get listening ports using netstat (fallback)."""
    ports_to_pids: dict[int, int] = {}

    try:
        if platform.system() == "Darwin":
            # macOS netstat
            result = subprocess.run(
                ["netstat", "-anv", "-p", "tcp"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        else:
            # Linux netstat
            result = subprocess.run(
                ["netstat", "-tlnp"],
                capture_output=True,
                text=True,
                timeout=10,
            )

        for line in result.stdout.strip().split("\n"):
            if "LISTEN" not in line:
                continue

            parts = line.split()

            try:
                if platform.system() == "Darwin":
                    # macOS format - look for local address and PID
                    # Proto Recv-Q Send-Q  Local Address  Foreign Address  (state)  ...  pid
                    if len(parts) >= 9:
                        local_addr = parts[3]
                        pid = int(parts[8])
                        if "." in local_addr:
                            port = int(local_addr.rsplit(".", 1)[-1])
                            ports_to_pids[port] = pid
                else:
                    # Linux format
                    if len(parts) >= 7:
                        local_addr = parts[3]
                        pid_prog = parts[6]
                        if ":" in local_addr and "/" in pid_prog:
                            port = int(local_addr.rsplit(":", 1)[-1])
                            pid = int(pid_prog.split("/")[0])
                            ports_to_pids[port] = pid
            except (ValueError, IndexError):
                continue

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return ports_to_pids


def get_listening_ports(dev_only: bool = True) -> list[PortInfo]:
    """Get all processes listening on ports.

    Args:
        dev_only: If True, only return ports in common dev server ranges.

    Returns:
        List of PortInfo objects sorted by port number.
    """
    # Try different methods to get port -> PID mapping
    ports_to_pids = _get_listening_ports_lsof()

    if not ports_to_pids:
        ports_to_pids = _get_listening_ports_ss()

    if not ports_to_pids:
        ports_to_pids = _get_listening_ports_netstat()

    ports: list[PortInfo] = []

    for port, pid in ports_to_pids.items():
        # Filter to dev ports if requested
        if dev_only and not is_dev_port(port):
            continue

        proc_info = _get_process_info(pid)
        if proc_info is None:
            continue

        port_info = PortInfo(
            port=port,
            pid=pid,
            name=proc_info["name"],
            cmdline=proc_info["cmdline"],
            process_type=identify_process_type(proc_info["name"]),
            framework=identify_framework(proc_info["cmdline"]),
            memory_mb=proc_info["memory_mb"],
            cpu_percent=proc_info["cpu_percent"],
            user=proc_info["user"],
            create_time=proc_info["create_time"],
        )
        ports.append(port_info)

    return sorted(ports, key=lambda p: p.port)


def get_port_info(port: int) -> PortInfo | None:
    """Get information about a specific port.

    Args:
        port: The port number to look up.

    Returns:
        PortInfo if a process is listening, None otherwise.
    """
    ports_to_pids = _get_listening_ports_lsof()

    if not ports_to_pids:
        ports_to_pids = _get_listening_ports_ss()

    if not ports_to_pids:
        ports_to_pids = _get_listening_ports_netstat()

    if port not in ports_to_pids:
        return None

    pid = ports_to_pids[port]
    proc_info = _get_process_info(pid)

    if proc_info is None:
        return None

    return PortInfo(
        port=port,
        pid=pid,
        name=proc_info["name"],
        cmdline=proc_info["cmdline"],
        process_type=identify_process_type(proc_info["name"]),
        framework=identify_framework(proc_info["cmdline"]),
        memory_mb=proc_info["memory_mb"],
        cpu_percent=proc_info["cpu_percent"],
        user=proc_info["user"],
        create_time=proc_info["create_time"],
    )


def kill_port(port: int, force: bool = False) -> tuple[bool, str]:
    """Kill the process listening on a port.

    Args:
        port: The port number.
        force: If True, use SIGKILL instead of SIGTERM.

    Returns:
        Tuple of (success, message).
    """
    port_info = get_port_info(port)

    if port_info is None:
        return False, f"No process found listening on port {port}"

    try:
        proc = psutil.Process(port_info.pid)
        sig = signal.SIGKILL if force else signal.SIGTERM
        os.kill(port_info.pid, sig)

        # Wait a bit for the process to terminate
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            if not force:
                # Try force kill if graceful shutdown didn't work
                os.kill(port_info.pid, signal.SIGKILL)
                proc.wait(timeout=2)

        return True, f"Killed {port_info.display_name} (PID {port_info.pid}) on port {port}"

    except psutil.NoSuchProcess:
        return True, f"Process on port {port} already terminated"
    except psutil.AccessDenied:
        return False, f"Permission denied: cannot kill process on port {port} (try with sudo)"
    except Exception as e:
        return False, f"Failed to kill process on port {port}: {e}"


def kill_ports(ports: list[int], force: bool = False) -> list[tuple[int, bool, str]]:
    """Kill multiple processes by port.

    Args:
        ports: List of port numbers.
        force: If True, use SIGKILL instead of SIGTERM.

    Returns:
        List of (port, success, message) tuples.
    """
    results = []
    for port in ports:
        success, message = kill_port(port, force)
        results.append((port, success, message))
    return results
