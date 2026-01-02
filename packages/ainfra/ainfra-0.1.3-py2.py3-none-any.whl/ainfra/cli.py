"""Command-line interface for AInfra."""
import functools
import importlib.util
import platform
import re
import subprocess
import sys
from importlib import import_module, metadata
from typing import List, Optional

VERSION_PATTERN = re.compile(r"v?\d+(\.\d+)*([a-zA-Z0-9\-\+\.]*)?")

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="ainfra",
    help="Simple way to pip install torch, vllm, flash-attn, sglang, ....",
    no_args_is_help=True,
)
console = Console()

# Supported libraries for installation
SUPPORTED_LIBRARIES = [
    {
        "name": "torch",
        "description": "PyTorch - Deep learning framework with GPU acceleration support",
        "doc_url": "https://pytorch.org/get-started/locally/",
        "module": "torch",
    },
    {
        "name": "vllm",
        "description": "vLLM - High-throughput and memory-efficient inference engine for LLMs",
        "doc_url": "https://docs.vllm.ai/en/stable/getting_started/installation/",
        "module": "vllm",
    },
    {
        "name": "numpy",
        "description": "NumPy - Fundamental package for scientific computing with Python",
        "doc_url": "https://numpy.org/install/",
        "module": "numpy",
    },
    {
        "name": "flash-attn",
        "description": "Flash Attention - Fast and memory-efficient exact attention",
        "doc_url": "https://github.com/Dao-AILab/flash-attention#installation",
        "module": "flash_attn",
        "package": "flash-attn",
    },
    {
        "name": "sglang",
        "description": "SGLang - Structured Generation Language for LLMs",
        "doc_url": "https://docs.sglang.io/get_started/install.html",
        "module": "sglang",
    },
    {
        "name": "liger-kernel",
        "description": "Liger Kernel - Optimized CUDA kernels for LLMs",
        "doc_url": "https://github.com/LinkSoul-AI/Liger-Kernel#installation",
        "module": "liger_kernel",
        "package": "liger-kernel",
    },
    {
        "name": "deepspeed",
        "description": "DeepSpeed - Deep learning optimization library for large-scale training",
        "doc_url": "https://www.deepspeed.ai/tutorials/installation/",
        "module": "deepspeed",
    },
    {
        "name": "transformers",
        "description": "Transformers - Hugging Face transformer library for NLP/LLM",
        "doc_url": "https://huggingface.co/docs/transformers/installation",
        "module": "transformers",
    },
]


def get_nvidia_driver_version() -> Optional[str]:
    """Get NVIDIA driver version."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_cuda_version() -> Optional[str]:
    """Get CUDA driver version."""
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Parse CUDA version from nvidia-smi output
            for line in result.stdout.split("\n"):
                if "CUDA Version:" in line:
                    # Extract version after "CUDA Version:"
                    parts = line.split("CUDA Version:")
                    if len(parts) > 1:
                        version = parts[1].strip().split()[0]
                        return version
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_os_info() -> str:
    """Get operating system information."""
    return f"{platform.system()} {platform.release()}"


def get_os_distribution() -> Optional[str]:
    """Get operating system distribution name (Ubuntu, CentOS, etc.)."""
    system = platform.system()
    
    if system == "Linux":
        try:
            # Try to read /etc/os-release for distribution info
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        # Extract the pretty name (split on first = only)
                        return line.split("=", 1)[1].strip().strip('"')
        except (FileNotFoundError, PermissionError):
            pass
    elif system == "Windows":
        return f"Windows {platform.release()}"
    elif system == "Darwin":
        return f"macOS {platform.mac_ver()[0]}"
    
    return None


def get_system_architecture() -> str:
    """Get system architecture (x86_64, ARM64, etc.)."""
    machine = platform.machine().lower()
    
    # Normalize common architecture names
    if machine in ["amd64", "x86_64", "x64"]:
        return "x86_64 / AMD64"
    elif machine in ["aarch64", "arm64"]:
        return "ARM64 / aarch64"
    elif machine.startswith("arm"):
        return f"ARM ({machine})"
    else:
        return machine


def get_python_version() -> str:
    """Get Python version."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


@functools.lru_cache(maxsize=None)
def get_install_status(package_name: str, module_name: Optional[str] = None) -> str:
    """Return installed status for a package, including version when available."""
    try:
        version = metadata.version(package_name)
        return version
    except metadata.PackageNotFoundError:
        pass

    module_to_check = module_name or package_name
    try:
        spec = importlib.util.find_spec(module_to_check)
    except ImportError:
        spec = None
    except ValueError:
        # Raised when the module name is malformed (e.g., contains path separators)
        spec = None

    if spec:
        try:
            module = import_module(module_to_check)
        except ImportError:
            return "Import error"

        for attr in ("__version__", "VERSION", "version"):
            version = getattr(module, attr, None)
            if version is None:
                continue
            version_text = str(version).strip()
            if version_text and VERSION_PATTERN.match(version_text):
                return version_text

        return "Installed"

    return "Not installed"


@app.command()
def info():
    """Display system information including Nvidia Driver, CUDA, OS, Architecture, and Python version."""
    table = Table(title="System Information", show_header=False)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    # Get system information
    nvidia_driver = get_nvidia_driver_version()
    cuda_version = get_cuda_version()
    os_info = get_os_info()
    os_distribution = get_os_distribution()
    architecture = get_system_architecture()
    python_version = get_python_version()

    # Add rows to table
    if os_distribution:
        table.add_row("Operating System", os_distribution)
        table.add_row("OS Version", os_info)
    else:
        # If we can't detect the distribution, just show OS info once
        table.add_row("Operating System", os_info)
    table.add_row("System Architecture", architecture)
    table.add_row("Python Version", python_version)
    table.add_row("Nvidia Driver Version", nvidia_driver if nvidia_driver else "Not detected")
    table.add_row("CUDA Driver Version", cuda_version if cuda_version else "Not detected")

    console.print(table)


@app.command()
def list():
    """List all supported libraries that can be installed."""
    table = Table(title="Supported Libraries", show_header=True)
    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Docs", style="blue", overflow="fold")

    for lib in SUPPORTED_LIBRARIES:
        # Use an explicit package name when it differs from the display name (e.g., flash-attn vs flash_attn)
        package_name = lib.get("package", lib["name"])
        status = get_install_status(package_name, lib.get("module"))
        docs_url = lib.get("doc_url")
        docs_link = f"[link={docs_url}]{docs_url}[/link]" if docs_url else "-"
        table.add_row(lib["name"], status, docs_link)

    console.print(table)
    console.print(f"\n[dim]Total: {len(SUPPORTED_LIBRARIES)} libraries[/dim]")


@app.command()
def install(
    packages: Optional[List[str]] = typer.Argument(None, help="Packages to install (e.g., torch, vllm, numpy) or 'all' for all packages"),
):
    """Install packages based on the local environment with user confirmation."""
    if not packages:
        console.print("[yellow]No packages specified. Use --help for usage information.[/yellow]")
        raise typer.Exit(1)

    # Check if "all" is requested
    if "all" in packages:
        packages_to_install = [lib["name"] for lib in SUPPORTED_LIBRARIES]
    else:
        packages_to_install = packages

    # Get system information for environment-based installation
    cuda_version = get_cuda_version()
    python_version = get_python_version()

    # Display what will be installed
    console.print("\n[bold cyan]Installation Plan:[/bold cyan]")
    console.print(f"[cyan]Environment:[/cyan]")
    console.print(f"  - Python Version: {python_version}")
    console.print(f"  - CUDA Version: {cuda_version if cuda_version else 'Not detected'}")
    
    console.print(f"\n[cyan]Packages to install:[/cyan]")
    for pkg in packages_to_install:
        console.print(f"  - {pkg}")

    # Ask for confirmation
    console.print()
    confirm = typer.confirm("Do you want to proceed with the installation?")
    
    if not confirm:
        console.print("[yellow]Installation cancelled.[/yellow]")
        raise typer.Exit(0)

    # Proceed with installation
    console.print("\n[bold green]Starting installation...[/bold green]")
    
    for package in packages_to_install:
        console.print(f"\n[cyan]Installing {package}...[/cyan]")
        
        # Determine the appropriate pip install command based on environment
        install_cmd = _get_install_command(package, cuda_version)
        
        console.print(f"[dim]Running: {' '.join(install_cmd)}[/dim]")
        
        try:
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                console.print(f"[green]✓ {package} installed successfully[/green]")
            else:
                console.print(f"[red]✗ Failed to install {package}[/red]")
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
        except Exception as e:
            console.print(f"[red]✗ Error installing {package}: {e}[/red]")
    
    console.print("\n[bold green]Installation complete![/bold green]")


def _get_install_command(package: str, cuda_version: Optional[str]) -> List[str]:
    """Get the appropriate pip install command based on package and environment."""
    base_cmd = [sys.executable, "-m", "pip", "install"]
    
    # Special handling for packages that need CUDA-specific versions
    if package == "torch":
        if cuda_version:
            # For CUDA-enabled systems, users typically need to specify the CUDA version
            # For now, we install the default which typically has CUDA support
            # Users can customize this for specific CUDA versions via PyTorch index-url
            return base_cmd + ["torch"]
        else:
            # For systems without CUDA, explicitly install CPU version
            return base_cmd + ["torch", "--index-url", "https://download.pytorch.org/whl/cpu"]
    
    # For other packages, use standard installation
    return base_cmd + [package]


if __name__ == "__main__":
    app()
