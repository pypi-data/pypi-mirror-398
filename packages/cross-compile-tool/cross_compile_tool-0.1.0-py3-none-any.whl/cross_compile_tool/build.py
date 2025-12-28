#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import shutil
import hashlib
import tempfile
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
# When installed as a package, we need to handle where we run from
WORKSPACE_DIR = Path.cwd()
DEFAULT_SYSROOT_DIR = WORKSPACE_DIR / "sysroot_arm64"
DEFAULT_BUILD_DIR = WORKSPACE_DIR / "build_arm64"
DEFAULT_PACKAGES_FILE = WORKSPACE_DIR / "apt_packages.txt"


def run_command(cmd, cwd=None, env=None):
    """Runs a shell command and streams output."""
    print(f"\n[CMD] {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd, cwd=cwd, env=env)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def get_file_hash(file_path):
    """Calculates MD5 hash of a file."""
    if not Path(file_path).exists():
        return None
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def build_sysroot(output_dir, packages_file, base_image, rebuild=False):
    """Builds and exports the sysroot using Docker."""
    print(f"\n[INFO] Building Sysroot from {base_image}...")

    # Ensure output directory exists
    output_dir = Path(output_dir).absolute()
    if output_dir.exists() and not rebuild:
        if (output_dir / "usr").exists():
            print(f"[INFO] Using existing sysroot at {output_dir}")
            return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare Package List
    src_deps = Path(packages_file).absolute()
    if not src_deps.exists():
        print(
            f"[WARNING] Packages file {src_deps} not found. Sysroot will only have base image contents."
        )
        packages_content = ""
    else:
        packages_content = src_deps.read_text()

    # 1. Build the Image
    # We use a hash of the packages file + base image to tag it uniquely if we wanted,
    # but for simplicity let's stick to a fixed tag per project context if possible,
    # or just "latest".
    image_tag = "cross-compile-sysroot:latest"

    # Use a temporary directory for build context to avoid writing to source tree
    with tempfile.TemporaryDirectory() as tmp_ctx:
        ctx_dir = Path(tmp_ctx)

        # Copy Dockerfile
        shutil.copy(SCRIPT_DIR / "Dockerfile", ctx_dir / "Dockerfile")

        # Create dependencies structure
        deps_dir = ctx_dir / "dependencies"
        deps_dir.mkdir()
        (deps_dir / "apt_packages_generated.txt").write_text(packages_content)

        cmd_build = [
            "docker",
            "build",
            "-t",
            image_tag,
            "--file",
            str(ctx_dir / "Dockerfile"),
            "--build-arg",
            f"BASE_IMAGE={base_image}",
            "--platform",
            "linux/arm64",
            str(ctx_dir),
        ]

        # Enable BuildKit
        env = os.environ.copy()
        env["DOCKER_BUILDKIT"] = "1"

        print("[INFO] Building Docker Image...")
        run_command(cmd_build, env=env)

    # 2. Sync Files
    print(f"[INFO] Syncing Sysroot to {output_dir}...")

    # Docker-in-Docker Path Remapping
    # If we are running inside a container, 'output_dir' (e.g. /ws/sysroot) doesn't exist on the Host.
    # The user must provide the Host's path to the workspace via HOST_WORKSPACE env var.
    host_ws = os.environ.get("HOST_WORKSPACE")
    if host_ws:
        # Relativize the output_dir to the current workspace (container side)
        try:
            rel_path = output_dir.relative_to(WORKSPACE_DIR)
            host_output_dir = Path(host_ws) / rel_path
            print(
                f"[INFO] Docker-in-Docker detected. Mapping container path '{output_dir}' to host path '{host_output_dir}'"
            )
        except ValueError:
            print(
                f"[WARNING] output_dir '{output_dir}' is not inside WORKSPACE_DIR '{WORKSPACE_DIR}'. Cannot remap for Docker-in-Docker."
            )
            host_output_dir = output_dir
    else:
        host_output_dir = output_dir

    cmd_sync = [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/arm64",
        "-v",
        f"{host_output_dir}:/target",
        image_tag,
        "rsync",
        "-aR",
        "--info=progress2",
        "--delete",
        "/lib",
        "/usr/include",
        "/usr/lib",
        "/usr/share",
        # "/opt/ros", # Generic now, but we should sync /opt just in case
        "/opt",
        "/etc",
        "/sysroot_manifest.txt",
        "/target/",
    ]

    run_command(cmd_sync)
    print(f"[INFO] Sysroot sync complete.")
    fix_symlinks(output_dir)

    # 3. Store Hash
    if src_deps.exists():
        current_hash = get_file_hash(src_deps)
        with open(output_dir / "sysroot.hash", "w") as f:
            f.write(current_hash)


def fix_symlinks(sysroot_dir):
    """Converts absolute symlinks in the sysroot to relative ones."""
    print("[INFO] Fixing absolute symlinks in sysroot...")
    sysroot = Path(sysroot_dir)
    count = 0
    # Walk carefully
    for link in sysroot.rglob("*"):
        if link.is_symlink():
            try:
                target = os.readlink(link)
                if target.startswith("/"):
                    # relative logic
                    rel_target_from_root = Path(target.lstrip("/"))
                    link_dir = link.parent
                    relative_root = os.path.relpath(sysroot, link_dir)
                    new_target = Path(relative_root) / rel_target_from_root
                    link.unlink()
                    link.symlink_to(new_target)
                    count += 1
            except OSError:
                pass
    print(f"[INFO] Fixed {count} absolute symlinks.")


def find_python_paths(sysroot_path):
    """Automatically detects Python paths in the sysroot."""
    sysroot = Path(sysroot_path)
    # Generic generic search
    include_candidates = list(sysroot.glob("usr/include/python3*"))
    if not include_candidates:
        # Might not be installed, which is valid for generic C++
        print("[WARNING] No Python headers found in sysroot. Python support disabled.")
        return None, None, None

    py_include = sorted(include_candidates)[-1]
    py_version = py_include.name

    # Library
    lib_candidates = list(sysroot.glob(f"usr/lib/aarch64-linux-gnu/lib{py_version}.so"))
    if not lib_candidates:
        lib_candidates = list(sysroot.glob(f"usr/lib/lib{py_version}.so"))

    if not lib_candidates:
        print(f"[WARNING] Headers found but lib{py_version}.so not found.")
        return None, None, None

    py_library = lib_candidates[0]

    version_match = py_version.replace("python", "")
    version_nodot = version_match.replace(".", "")
    return py_library, version_match, version_nodot


def ensure_system_python_symlink(sysroot_lib):
    """Creates symlink to trick CMake into finding sysroot python as system python."""
    if not sysroot_lib:
        return
    try:
        parts = sysroot_lib.parts
        if "usr" in parts and "lib" in parts:
            idx = parts.index("lib")
            suffix = Path(*parts[idx + 1 :])
            system_path = Path("/usr/lib") / suffix

            if not system_path.exists():
                print(f"[INFO] Creating system symlink: {system_path}")
                try:
                    system_path.parent.mkdir(parents=True, exist_ok=True)
                    system_path.symlink_to(sysroot_lib)
                except PermissionError:
                    print(
                        f"[WARN] Failed to create symlink {system_path}. Sudo required? ignoring."
                    )
    except Exception:
        pass


def check_environment(needs_docker=True):
    """Verifies that the necessary tools are installed."""
    # 1. Check for Cross Compiler (Crucial for the build step)
    if not needs_docker and not shutil.which("aarch64-linux-gnu-g++"):
        print("[ERROR] Cross-compiler 'aarch64-linux-gnu-g++' not found.")
        print("        Please install it: sudo apt install g++-aarch64-linux-gnu")
        sys.exit(1)

    # 2. Check for Docker (Needed for sysroot generation)
    if needs_docker and not shutil.which("docker"):
        print("[ERROR] 'docker' command not found.")
        print("        Docker is required to build the sysroot.")
        sys.exit(1)


def handle_sysroot(args):
    """Handle the sysroot subcommand."""
    sysroot_path = Path(args.sysroot).absolute()

    # We always check environment if explicitly building sysroot
    check_environment(needs_docker=True)

    build_sysroot(
        sysroot_path, args.packages_file, args.base_image, rebuild=args.rebuild
    )


def check_sysroot_staleness(sysroot_dir, packages_file):
    """Checks if the packages file has changed since last sysroot build."""
    packages_path = Path(packages_file)
    sysroot_path = Path(sysroot_dir)
    hash_file = sysroot_path / "sysroot.hash"

    if not packages_path.exists():
        return False

    if not sysroot_path.exists() or not (sysroot_path / "usr").exists():
        return True

    current_hash = get_file_hash(packages_path)

    if not hash_file.exists():
        # Fallback to timestamp if no hash (migration path)
        try:
            if packages_path.stat().st_mtime > sysroot_path.stat().st_mtime:
                print(f"[WARNING] {packages_file} is newer than sysroot (timestamp).")
                return True
        except OSError:
            pass
        return False

    stored_hash = hash_file.read_text().strip()
    if current_hash != stored_hash:
        print(f"[WARNING] {packages_file} content has changed (hash mismatch).")
        print(
            f"          Runtime: {stored_hash[:8]}... vs Current: {current_hash[:8]}..."
        )
        print(f"          Run 'sysroot --rebuild' to update.")
        return True

    return False


def handle_build(args):
    """Handle the build subcommand."""
    sysroot_path = Path(args.sysroot).absolute()

    # 1. Lazy Sysroot Check
    if not (sysroot_path / "usr").exists():
        print(f"[INFO] Sysroot not found at {sysroot_path}. Auto-building...")
        check_environment(needs_docker=True)
        build_sysroot(sysroot_path, args.packages_file, args.base_image, rebuild=False)
    else:
        # Just warn if possibly stale
        check_sysroot_staleness(sysroot_path, args.packages_file)
        # We don't enforce docker check here, effectively making it "native only" if sysroot exists
        check_environment(needs_docker=False)

    # 2. Python Setup (Dynamic)
    py_lib, py_ver, py_nodot = find_python_paths(sysroot_path)
    ensure_system_python_symlink(py_lib)

    # 3. Build Logic
    has_colcon = shutil.which("colcon") is not None
    tool = args.build_tool

    if tool == "auto":
        tool = "colcon" if has_colcon else "cmake"
        print(f"[INFO] Auto-detected build tool: {tool}")

    toolchain_file = SCRIPT_DIR / "toolchain.cmake"

    env_vars = os.environ.copy()
    env_vars["TARGET_SYSROOT"] = str(sysroot_path)
    if py_ver:
        env_vars["PYTHON_VERSION"] = py_ver
        env_vars["PYTHON_VERSION_NODOT"] = py_nodot

    # CLEAN
    if args.clean:
        if Path(args.build_dir).exists():
            shutil.rmtree(args.build_dir)
        # also clean install for colcon
        install_dir = Path(args.build_dir).parent / "install_arm64"
        if install_dir.exists():
            shutil.rmtree(install_dir)

    print(f"[INFO] Building with {tool}...")

    if tool == "colcon":
        # Check if we have ros source in sysroot to determine cmake prefix path
        ros_prefixes = list(sysroot_path.glob("opt/ros/*"))
        cmake_prefix = f"{sysroot_path}/usr"
        if ros_prefixes:
            for p in ros_prefixes:
                cmake_prefix = f"{p};{cmake_prefix}"

        colcon_cmd = [
            "colcon",
            "build",
            "--build-base",
            str(args.build_dir),
            "--install-base",
            str(Path(args.build_dir).parent / "install_arm64"),
            "--merge-install",
            "--cmake-args",
            "-G",
            "Ninja",
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_file}",
            f"-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_PREFIX_PATH={cmake_prefix}",
            "--event-handlers",
            "console_direct+",
        ]
        run_command(colcon_cmd, env=env_vars)

    elif tool == "cmake":
        build_path = Path(args.build_dir)
        build_path.mkdir(parents=True, exist_ok=True)

        cmake_config = [
            "cmake",
            "-S",
            str(WORKSPACE_DIR),
            "-B",
            str(build_path),
            "-G",
            "Ninja",
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_file}",
            f"-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_PREFIX_PATH={sysroot_path}/usr",
            f"-DCMAKE_SYSROOT={sysroot_path}",
        ]
        run_command(cmake_config, env=env_vars)
        run_command(["cmake", "--build", str(build_path)], env=env_vars)


def handle_build_docker_dev(args):
    """Build the CI/Dev Docker image using the packaged Dockerfile."""
    src_dockerfile = SCRIPT_DIR / "dev.Dockerfile"
    if not src_dockerfile.exists():
        print("[ERROR] Could not find source dev.Dockerfile in package.")
        sys.exit(1)

    tag = args.tag
    base_image = args.base_image
    print(
        f"[INFO] Building Dev Container '{tag}' from '{base_image}' using internal Dockerfile..."
    )

    # We can build directly referring to the file in site-packages
    cmd = [
        "docker",
        "build",
        "-t",
        tag,
        "-f",
        str(src_dockerfile),
        "--build-arg",
        f"BASE_IMAGE={base_image}",
        ".",
    ]
    run_command(cmd)

    print(f"\n[SUCCESS] Built '{tag}'. Run it with:")
    print(
        f"  docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock -v $(pwd):/ws -e HOST_WORKSPACE=$(pwd) {tag}"
    )


def main():
    parser = argparse.ArgumentParser(description="Generic Fast Cross-Compile Tool")

    # Global arguments
    parser.add_argument(
        "--sysroot", default=str(DEFAULT_SYSROOT_DIR), help="Path to sysroot"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    subparsers.required = True

    # Subcommand: sysroot
    parser_sysroot = subparsers.add_parser("sysroot", help="Manage sysroot environment")
    parser_sysroot.add_argument(
        "--rebuild", action="store_true", help="Force rebuild of sysroot"
    )
    parser_sysroot.add_argument(
        "--base-image",
        default="ubuntu:22.04",
        help="Docker base image (e.g. ubuntu:22.04 or ros:humble-ros-base)",
    )
    parser_sysroot.add_argument(
        "--packages-file",
        default=str(DEFAULT_PACKAGES_FILE),
        help="Apt packages list file",
    )
    parser_sysroot.set_defaults(func=handle_sysroot)

    # Subcommand: build
    parser_build = subparsers.add_parser("build", help="Compile the code")
    parser_build.add_argument(
        "--build-dir", default=str(DEFAULT_BUILD_DIR), help="Build directory"
    )
    parser_build.add_argument(
        "--clean", action="store_true", help="Clean build directory"
    )
    parser_build.add_argument(
        "--build-tool",
        choices=["auto", "colcon", "cmake"],
        default="auto",
        help="Build tool to use",
    )
    parser_build.add_argument(
        "--packages-file",
        default=str(DEFAULT_PACKAGES_FILE),
        help="Apt packages list file (for staleness check only)",
    )
    # Allows build command to also accept base-image in case it needs to auto-build sysroot
    parser_build.add_argument(
        "--base-image",
        default="ubuntu:22.04",
        help="Docker base image (if auto-building sysroot)",
    )
    parser_build.set_defaults(func=handle_build)

    # Subcommand: build-dev
    parser_dev = subparsers.add_parser(
        "build-dev", help="Build the CI/Dev Docker image"
    )
    parser_dev.add_argument(
        "--tag", default="my-ci-image", help="Tag for the generated image"
    )
    parser_dev.add_argument(
        "--base-image", default="ros:humble", help="Base image for the dev container"
    )
    parser_dev.set_defaults(func=handle_build_docker_dev)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
