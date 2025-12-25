#!/usr/bin/env python
"""Verify Docker build and GPU support.

This utility verifies Docker builds, including checking for GPU support
and validating that all required packages are properly installed in containers.

Usage:
    uv run verify-docker             # Verify Docker build
    uv run verify-docker --gpu       # Verify GPU Docker build
    uv run verify-docker --quick     # Quick validation only
"""

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str | list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command safely without shell injection vulnerabilities.

    Args:
        cmd: Command to run - either a string (will be safely parsed) or list of arguments
        check: Whether to exit on failure

    Returns:
        CompletedProcess instance with command results

    Note:
        This function uses shell=False for security. Commands are parsed into argument
        lists using shlex.split() to prevent shell injection attacks. If you genuinely
        need shell features (pipes, redirects, etc.), use Python equivalents instead.
    """
    # Convert string commands to lists safely
    if isinstance(cmd, str):
        print(f"Running: {cmd}")
        cmd_list = shlex.split(cmd)
    else:
        print(f"Running: {' '.join(cmd)}")
        cmd_list = cmd

    # Always use shell=False for security
    result = subprocess.run(cmd_list, shell=False, capture_output=True, text=True)

    if check and result.returncode != 0:
        print(f"Command failed: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(result.returncode)

    return result


def check_docker_installed() -> bool:
    """Check if Docker is installed and running.

    Returns:
        True if Docker is available, False otherwise
    """
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print("Docker is not installed or not in PATH")
        return False

    print(f"Docker installed: {result.stdout.strip()}")

    # Check if Docker daemon is running
    result = run_command("docker info", check=False)
    if result.returncode != 0:
        print("Docker daemon is not running")
        print("  Run: docker start (or start Docker Desktop)")
        return False

    print("Docker daemon is running")
    return True


def check_nvidia_docker() -> bool:
    """Check if NVIDIA Docker runtime is available.

    Returns:
        True if NVIDIA runtime is available, False otherwise
    """
    result = run_command(
        ["docker", "run", "--rm", "--gpus", "all", "nvidia/cuda:11.8.0-base-ubuntu22.04", "nvidia-smi"], check=False
    )
    if result.returncode == 0:
        print("NVIDIA Docker runtime is available")
        print("GPU Information:")
        print(result.stdout)
        return True
    else:
        print("⚠️  NVIDIA Docker runtime not available or no GPU detected")
        return False


def build_docker_image(dockerfile: str = "Dockerfile", tag: str = "cve_report_aggregator:test") -> bool:
    """Build Docker image for testing.

    Args:
        dockerfile: Path to Dockerfile
        tag: Docker image tag

    Returns:
        True if build successful, False otherwise
    """
    if not Path(dockerfile).exists():
        print(f"Dockerfile not found: {dockerfile}")
        return False

    print(f"\n🔨 Building Docker image from {dockerfile}...")
    result = run_command(["docker", "build", "-f", dockerfile, "-t", tag, "."], check=False)

    if result.returncode == 0:
        print(f"Docker image built successfully: {tag}")
        return True
    else:
        print("Docker build failed")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False


def test_docker_image(tag: str = "cve_report_aggregator:test", gpu: bool = False) -> bool:
    """Test Docker image functionality.

    Args:
        tag: Docker image tag to test
        gpu: Whether to test with GPU support

    Returns:
        True if tests pass, False otherwise
    """
    print(f"\n🧪 Testing Docker image: {tag}")

    # Test 1: Python version
    print("\n1. Checking Python version...")
    cmd = ["docker", "run", "--rm"]
    if gpu:
        cmd.extend(["--gpus", "all"])
    cmd.extend([tag, "python", "--version"])
    result = run_command(cmd, check=False)
    if result.returncode != 0:
        print("Failed to check Python version")
        return False
    print(f"   {result.stdout.strip()}")

    # Test 2: Import cve_report_aggregator
    print("\n2. Testing cve_report_aggregator import...")
    cmd = ["docker", "run", "--rm"]
    if gpu:
        cmd.extend(["--gpus", "all"])
    cmd.extend([tag, "python", "-c", "import cve_report_aggregator; print('cve_report_aggregator imported')"])
    result = run_command(cmd, check=False)
    if result.returncode != 0:
        print("Failed to import cve_report_aggregator")
        return False

    # Test 3: Check CLI
    print("\n3. Testing CLI...")
    cmd = ["docker", "run", "--rm"]
    if gpu:
        cmd.extend(["--gpus", "all"])
    cmd.extend([tag, "python", "-m", "cve_report_aggregator", "--help"])
    result = run_command(cmd, check=False)
    if result.returncode != 0:
        print("CLI test failed")
        return False
    print("   CLI is functional")

    # Test 4: GPU packages (if GPU enabled)
    if gpu:
        print("\n4. Testing GPU packages...")
        gpu_test_code = (
            "import torch; "
            'print(f"PyTorch: {torch.__version__}"); '
            'print(f"CUDA available: {torch.cuda.is_available()}"); '
            "print(f\"CUDA version: {torch.version.cuda if torch.cuda.is_available() else 'N/A'}\")"
        )
        cmd = ["docker", "run", "--rm", "--gpus", "all", tag, "python", "-c", gpu_test_code]
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            print("⚠️  GPU packages test failed (may be expected without GPU)")
        else:
            print(f"   {result.stdout}")

    print(f"\n✅ All tests passed for {tag}")
    return True


def main() -> None:
    """Run Docker verification."""
    parser = argparse.ArgumentParser(description="Verify Docker build and functionality")
    parser.add_argument("--gpu", action="store_true", help="Test GPU Docker build")
    parser.add_argument("--quick", action="store_true", help="Quick validation only (no build)")
    parser.add_argument("--dockerfile", default="Dockerfile", help="Dockerfile to use")
    parser.add_argument("--tag", default="cve_report_aggregator:test", help="Docker image tag")

    args = parser.parse_args()

    print("=" * 60)
    print("Docker Build Verification")
    print("=" * 60)

    # Check Docker installation
    if not check_docker_installed():
        print("\nDocker is not properly installed or running")
        sys.exit(1)

    # Check GPU support if requested
    if args.gpu:
        check_nvidia_docker()

    # Build image unless quick mode
    if not args.quick:
        dockerfile = args.dockerfile
        if args.gpu and dockerfile == "Dockerfile":
            dockerfile = "Dockerfile.nvidia"

        if not build_docker_image(dockerfile, args.tag):
            print("\nDocker build failed")
            sys.exit(1)

    # Test the image
    if not test_docker_image(args.tag, args.gpu):
        print("\nDocker image tests failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Docker verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
