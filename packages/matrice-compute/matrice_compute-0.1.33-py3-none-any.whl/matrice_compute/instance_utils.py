"""Module providing instance utilities functionality."""

import os
import socket
import urllib.request
import subprocess
import logging
import base64
from datetime import datetime
import psutil
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)
from cryptography.hazmat.backends import default_backend
from matrice_common.utils import log_errors


def get_instance_info(service_provider: str = None, instance_id: str = None) -> tuple:
    """
    Get instance provider and ID information.

    Returns:
        tuple: (service_provider, instance_id) strings
    """
    auto_service_provider = service_provider or os.environ.get("SERVICE_PROVIDER") or "LOCAL"
    auto_instance_id = instance_id or os.environ.get("INSTANCE_ID") or ""
    try:
        gcp_check = subprocess.run(
            "curl -s -m 1 -H 'Metadata-Flavor: Google' 'http://metadata.google.internal/computeMetadata/v1/instance/id'",
            shell=True,
            capture_output=True,
            check=True,
        )
        if gcp_check.returncode == 0:
            auto_service_provider = "GCP"
            auto_instance_id = gcp_check.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    try:
        azure_check = subprocess.run(
            "curl -s -m 1 -H Metadata:true 'http://169.254.169.254/metadata/instance?api-version=2020-09-01'",
            shell=True,
            capture_output=True,
            check=True,
        )
        if azure_check.returncode == 0:
            auto_service_provider = "AZURE"
            azure_id = subprocess.run(
                "curl -s -H Metadata:true 'http://169.254.169.254/metadata/instance/compute/vmId?api-version=2017-08-01&format=text'",
                shell=True,
                capture_output=True,
                check=True,
            )
            auto_instance_id = azure_id.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    try:
        oci_check = subprocess.run(
            "curl -s -m 1 -H 'Authorization: Bearer OracleCloud' 'http://169.254.169.254/opc/v1/instance/'",
            shell=True,
            capture_output=True,
            check=True,
        )
        if oci_check.returncode == 0:
            auto_service_provider = "OCI"
            oci_id = subprocess.run(
                "curl -s http://169.254.169.254/opc/v1/instance/id",
                shell=True,
                capture_output=True,
                check=True,
            )
            auto_instance_id = oci_id.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    try:
        aws_check = subprocess.run(
            "curl -s -m 1 http://169.254.169.254/latest/meta-data/",
            shell=True,
            capture_output=True,
            check=True,
        )
        if aws_check.returncode == 0:
            auto_service_provider = "AWS"
            aws_id = subprocess.run(
                "curl -s http://169.254.169.254/latest/meta-data/instance-id",
                shell=True,
                capture_output=True,
                check=True,
            )
            auto_instance_id = aws_id.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    return str(auto_service_provider), str(auto_instance_id)


def _normalize_timestamp(timestamp_str: str) -> str:
    """
    Normalize timestamp string to handle different precision levels.
    
    Handles nanoseconds (9 digits), microseconds (6 digits), milliseconds (3 digits),
    and various timezone formats across different cloud providers.
    
    Args:
        timestamp_str (str): Timestamp string in various formats
        
    Returns:
        str: Normalized timestamp string compatible with fromisoformat()
    """
    # Replace 'Z' with '+00:00' for UTC timestamps
    timestamp_str = timestamp_str.replace("Z", "+00:00")
    
    # Handle fractional seconds - Python's datetime only supports up to 6 digits (microseconds)
    # Some providers (like OCI, GCP) may return nanoseconds (9 digits)
    if "." in timestamp_str:
        # Split into main part and fractional part
        if "+" in timestamp_str:
            main_part, tz_part = timestamp_str.rsplit("+", 1)
            tz_suffix = "+" + tz_part
        elif timestamp_str.count("-") > 2:  # Has negative timezone offset
            main_part, tz_part = timestamp_str.rsplit("-", 1)
            tz_suffix = "-" + tz_part
        else:
            main_part = timestamp_str
            tz_suffix = ""
        
        # Split main part into date/time and fractional seconds
        datetime_part, fractional = main_part.rsplit(".", 1)
        
        # Truncate fractional seconds to 6 digits (microseconds)
        if len(fractional) > 6:
            fractional = fractional[:6]
        
        # Reconstruct timestamp
        timestamp_str = f"{datetime_part}.{fractional}{tz_suffix}"
    
    return timestamp_str


@log_errors(default_return=0, raise_exception=False, log_error=False)
def calculate_time_difference(start_time_str: str, finish_time_str: str) -> int:
    """
    Calculate time difference between start and finish times.
    
    Robust handling of timestamps from different cloud providers (AWS, GCP, Azure, OCI)
    and different precision levels (nanoseconds, microseconds, milliseconds).

    Args:
        start_time_str (str): Start time string in ISO format
        finish_time_str (str): Finish time string in ISO format

    Returns:
        int: Time difference in seconds
    """
    # Normalize both timestamps to handle different formats
    normalized_start = _normalize_timestamp(start_time_str)
    normalized_finish = _normalize_timestamp(finish_time_str)
    
    # Parse the normalized timestamps
    start_time = datetime.fromisoformat(normalized_start)
    finish_time = datetime.fromisoformat(normalized_finish)
    
    return int((finish_time - start_time).total_seconds())


@log_errors(default_return=False, raise_exception=False, log_error=False)
def has_gpu() -> bool:
    """
    Check if the system has a GPU.

    Returns:
        bool: True if GPU is present, False otherwise
    """
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logging.debug("nvidia-smi command timed out after 5 seconds")
        return False
    except FileNotFoundError:
        logging.debug("nvidia-smi not found on this system")
        return False
    except Exception:
        return False


@log_errors(default_return=0, raise_exception=False, log_error=False)
def get_gpu_memory_usage() -> float:
    """
    Get GPU memory usage percentage.

    Returns:
        float: Memory usage between 0 and 1
    """
    command = ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,nounits,noheader"]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            logging.debug("nvidia-smi command failed in get_gpu_memory_usage")
            return 0
        output = result.stdout.decode("ascii").strip().split("\n")
        memory_percentages = []
        for line in output:
            if line.strip():
                used, total = map(int, line.split(","))
                if total > 0:
                    usage_percentage = used / total
                    memory_percentages.append(usage_percentage)
        return min(memory_percentages) if memory_percentages else 0
    except subprocess.TimeoutExpired:
        logging.debug("nvidia-smi command timed out after 5 seconds in get_gpu_memory_usage")
        return 0
    except (ValueError, IndexError) as e:
        logging.debug("Error parsing GPU memory info: %s", e)
        return 0
    except Exception as e:
        logging.debug("Unexpected error in get_gpu_memory_usage: %s", e)
        return 0


@log_errors(default_return=0, raise_exception=False)
def get_cpu_memory_usage() -> float:
    """
    Get CPU memory usage.

    Returns:
        float: Memory usage between 0 and 1
    """
    memory = psutil.virtual_memory()
    return memory.percent / 100


@log_errors(default_return=0, raise_exception=False)
def get_mem_usage() -> float:
    """
    Get memory usage for either GPU or CPU.

    Returns:
        float: Memory usage between 0 and 1
    """
    if has_gpu():
        try:
            mem_usage = get_gpu_memory_usage()
        except Exception as err:
            logging.error(
                "Error getting GPU memory usage: %s",
                err,
            )
            mem_usage = get_cpu_memory_usage()
    else:
        mem_usage = get_cpu_memory_usage()
    if mem_usage is None:
        mem_usage = 0
    return mem_usage


@log_errors(default_return=[], raise_exception=False, log_error=False)
def get_gpu_info() -> list:
    """
    Get GPU information.

    Returns:
        list: GPU information strings
    """
    try:
        proc = subprocess.Popen(
            [
                "nvidia-smi",
                "--query-gpu=index,uuid,utilization.gpu,memory.total,memory.used,memory.free,driver_version,name,gpu_serial,display_active,display_mode,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = proc.communicate(timeout=5)
            if proc.returncode != 0:
                logging.debug("nvidia-smi command failed in get_gpu_info")
                return []
            output = stdout.decode("UTF-8")
            result = [line for line in output.split("\n") if line.strip()]
            return result
        except subprocess.TimeoutExpired:
            logging.debug("nvidia-smi command timed out after 5 seconds in get_gpu_info")
            proc.kill()
            proc.communicate()  # flush output after kill
            return []
    except FileNotFoundError:
        logging.debug("nvidia-smi not found on this system")
        return []
    except Exception as e:
        logging.debug("Error getting GPU info: %s", e)
        return []


@log_errors(default_return="", raise_exception=False)
def get_instance_id() -> str:
    """
    Get instance ID.

    Returns:
        str: Instance ID or empty string
    """
    return os.environ["INSTANCE_ID"]


@log_errors(default_return=False, raise_exception=False, log_error=False)
def is_docker_running() -> bool:
    """
    Check if Docker is running.

    Returns:
        bool: True if Docker containers are running
    """
    command = ["docker", "ps"]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
        if result.returncode != 0:
            logging.warning("docker ps command failed")
            return False
        docker_images = result.stdout.decode("ascii").split("\n")[:-1][1:]
        return bool(docker_images)
    except subprocess.TimeoutExpired:
        logging.warning("docker ps command timed out")
        return False
    except FileNotFoundError:
        logging.warning("docker command not found")
        return False
    except Exception as e:
        logging.warning("Error checking if docker is running: %s", e)
        return False


@log_errors(default_return=None, raise_exception=False)
def prune_docker_images() -> None:
    """Prune Docker images."""
    subprocess.run(
        [
            "docker",
            "image",
            "prune",
            "-a",
            "-f",
        ],
        check=True,
    )
    logging.info("Docker images pruned successfully.")


@log_errors(default_return=0.0, raise_exception=False)
def _normalize_disk_usage_to_gb(disk_space: str) -> float:
    """
    Normalize disk usage to GB.

    Args:
        disk_space (str): Disk space with unit

    Returns:
        float: Disk space in GB
    """
    if disk_space.endswith("G"):
        result = float(disk_space[:-1])
    elif disk_space.endswith("T"):
        result = float(disk_space[:-1]) * 1024
    elif disk_space.endswith("M"):
        result = float(disk_space[:-1]) / 1024
    elif disk_space.endswith("K"):
        result = float(disk_space[:-1]) / (1024 * 1024)
    else:
        result = float(disk_space)
    logging.debug(
        "Normalized disk space value to %f GB",
        result,
    )
    return result


@log_errors(default_return=None, raise_exception=False)
def _parse_disk_usage_info(line: str) -> dict:
    """
    Parse disk usage information.

    Args:
        line (str): Disk usage line from df command

    Returns:
        dict: Parsed disk usage information
    """
    parts = line.split()
    parsed_info = {
        "filesystem": parts[0],
        "size": _normalize_disk_usage_to_gb(parts[1]),
        "used": _normalize_disk_usage_to_gb(parts[2]),
        "available": _normalize_disk_usage_to_gb(parts[3]),
        "use_percentage": float(parts[4].rstrip("%")),
        "mounted_on": parts[5],
    }
    logging.debug(
        "Successfully parsed disk usage info: %s",
        parsed_info,
    )
    return parsed_info


@log_errors(default_return=None, raise_exception=False)
def get_disk_space_usage() -> list:
    """
    Get disk space usage for all filesystems.

    Returns:
        list: List of disk usage information dictionaries
    """
    logging.info("Getting disk space usage information")
    result = subprocess.run(
        ["df", "-h"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split("\n")[1:]
    disk_usage = []
    for line in lines:
        disk = _parse_disk_usage_info(line)
        if disk:
            disk_usage.append(disk)
    logging.info(
        "Found disk usage info for %d filesystems",
        len(disk_usage),
    )
    return disk_usage


@log_errors(default_return=None, raise_exception=False)
def get_max_file_system() -> str:
    """
    Get filesystem with maximum available space.

    Returns:
        str: Path to filesystem with most space or None
    """
    logging.info("Finding filesystem with maximum available space")
    disk_usage = get_disk_space_usage()
    if not disk_usage:
        logging.warning("No disk usage information available")
        return None
    filtered_disks = [
        disk
        for disk in disk_usage
        if disk["mounted_on"] != "/boot/efi"
        and "overlay" not in disk["filesystem"]
        and disk["available"] > 0
    ]
    if not filtered_disks:
        logging.warning("No suitable filesystems found after filtering")
        max_available_filesystem = ""
    else:
        max_disk = max(
            filtered_disks,
            key=lambda x: x["available"],
        )
        max_available_filesystem = max_disk["mounted_on"]
        logging.info(
            "Found filesystem with maximum space: %s (%f GB available)",
            max_available_filesystem,
            max_disk["available"],
        )
    # Check if filesystem is writable, or if it's root/empty
    if max_available_filesystem in ["/", ""] or not os.access(max_available_filesystem, os.W_OK):
        if max_available_filesystem not in ["/", ""]:
            logging.warning(
                "Filesystem %s is not writable, falling back to home directory",
                max_available_filesystem,
            )
        home_dir = os.path.expanduser("~")
        if not os.environ.get("WORKSPACE_DIR"):
            logging.error("WORKSPACE_DIR environment variable not set")
            return None
        workspace_dir = os.path.join(
            home_dir,
            os.environ["WORKSPACE_DIR"],
        )
        os.makedirs(workspace_dir, exist_ok=True)
        logging.info(
            "Created workspace directory at: %s",
            workspace_dir,
        )
        return workspace_dir
    return max_available_filesystem


@log_errors(default_return=None, raise_exception=False)
def get_docker_disk_space_usage() -> dict:
    """
    Get disk space usage for Docker storage.

    Returns:
        dict: Docker disk usage information
    """
    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        check=True,
    )
    docker_info = result.stdout
    docker_root_dir = None
    for line in docker_info.split("\n"):
        if line.strip().startswith("Docker Root Dir"):
            docker_root_dir = line.split(":")[1].strip()
            break
    if docker_root_dir is None:
        logging.error("Unable to find Docker root directory")
        raise ValueError("Unable to find Docker root directory")
    logging.debug(
        "Found Docker root directory: %s",
        docker_root_dir,
    )
    result = subprocess.run(
        ["df", "-h", docker_root_dir],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().split("\n")[1:]
    if not lines:
        logging.error("No disk usage information found for Docker root directory")
        raise ValueError("No disk usage information found for Docker root directory")
    docker_disk_usage = _parse_disk_usage_info(lines[0])
    if docker_disk_usage is None:
        logging.error("Failed to parse Docker disk usage information")
        raise ValueError("Failed to parse Docker disk usage information")
    logging.info(
        "Successfully retrieved Docker disk usage: %s",
        docker_disk_usage,
    )
    return docker_disk_usage


@log_errors(raise_exception=False)
def cleanup_docker_storage() -> None:
    """Clean up Docker storage if space is low."""
    docker_disk_usage = get_docker_disk_space_usage()
    if docker_disk_usage is None:
        logging.error("Failed to get Docker disk space usage, skipping cleanup")
        return
    if docker_disk_usage["use_percentage"] >= 90 or docker_disk_usage["available"] <= 30:
        logging.info(
            "Pruning Docker images. Disk space is low: %s",
            docker_disk_usage,
        )
        prune_docker_images()


@log_errors(default_return=0, raise_exception=False)
def get_required_gpu_memory(action_details: dict) -> int:
    """
    Get required GPU memory from action details.

    Args:
        action_details (dict): Action details

    Returns:
        int: Required GPU memory
    """
    try:
        return action_details["actionDetails"]["expectedResources"]["gpuMemory"]
    except KeyError:
        return 0


@log_errors(default_return=True, raise_exception=False)
def is_allowed_gpu_device(gpu_index: int) -> bool:
    """Check if GPU device is allowed based on GPUS environment variable.

    The GPUS environment variable can be used to restrict which GPU devices
    are available for allocation (e.g., GPUS="0,2" allows only GPU 0 and 2).

    Args:
        gpu_index (int): GPU device index

    Returns:
        bool: True if GPU is allowed (or no filter is set), False otherwise
    """
    gpus = os.environ.get("GPUS", "").strip()
    # No filter set or empty string - all GPUs are allowed
    if not gpus or gpus == '""' or gpus == "''":
        return True

    try:
        allowed_gpus = [int(x.strip()) for x in gpus.split(",") if x.strip()]

        # If no valid GPUs after parsing, allow all
        if not allowed_gpus:
            return True

        is_allowed = int(gpu_index) in allowed_gpus

        if not is_allowed:
            logging.debug(
                "GPU %d is not in allowed GPU list: %s",
                gpu_index,
                allowed_gpus
            )

        return is_allowed

    except ValueError as e:
        logging.warning(
            "Invalid GPUS environment variable format '%s': %s. Allowing all GPUs.",
            gpus,
            e
        )
        return True


@log_errors(raise_exception=True, log_error=False)
def get_gpu_with_sufficient_memory_for_action(
    action_details: dict,
) -> list:
    """
    Get GPUs with sufficient memory for action.

    Args:
        action_details (dict): Action details

    Returns:
        list: List of GPU indices

    Raises:
        ValueError: If insufficient GPU memory
    """
    action_id = action_details.get("_id", "unknown")
    required_gpu_memory = get_required_gpu_memory(action_details)

    logging.info(
        "Action %s: Searching for GPU(s) with %d MB available memory",
        action_id,
        required_gpu_memory
    )

    command = ["nvidia-smi", "--query-gpu=memory.free", "--format=csv"]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            error_msg = f"nvidia-smi command failed with return code {result.returncode}"
            logging.error("Action %s: %s", action_id, error_msg)
            raise ValueError("Failed to get GPU information - nvidia-smi command failed")
        memory_free_info = result.stdout.decode("ascii").strip().split("\n")
    except subprocess.TimeoutExpired:
        logging.error(
            "Action %s: nvidia-smi command timed out after 5 seconds",
            action_id
        )
        raise ValueError("Failed to get GPU information - nvidia-smi timed out")
    except FileNotFoundError:
        logging.error(
            "Action %s: nvidia-smi not found on this system",
            action_id
        )
        raise ValueError("nvidia-smi not found - no GPU support available")
    except Exception as e:
        logging.error(
            "Action %s: Error running nvidia-smi: %s",
            action_id,
            e
        )
        raise ValueError(f"Failed to get GPU information: {e}")

    if len(memory_free_info) < 2:
        logging.error(
            "Action %s: No GPU information available from nvidia-smi output",
            action_id
        )
        raise ValueError("No GPU information available from nvidia-smi")

    try:
        memory_free_values = [int(x.split()[0]) for x in memory_free_info[1:] if x.strip()]
    except (ValueError, IndexError) as e:
        logging.error(
            "Action %s: Error parsing GPU memory information: %s",
            action_id,
            e
        )
        raise ValueError(f"Error parsing GPU memory information: {e}")

    if not memory_free_values:
        logging.error("Action %s: No GPU devices found", action_id)
        raise ValueError("No GPU devices found")

    # Log all available GPUs and their free memory
    logging.info(
        "Action %s: Found %d GPU(s) - Free memory: %s",
        action_id,
        len(memory_free_values),
        ", ".join([f"GPU{i}: {mem}MB" for i, mem in enumerate(memory_free_values)])
    )

    # Check GPUS environment variable for allowed devices
    allowed_gpus = os.environ.get("GPUS", "")
    if allowed_gpus:
        logging.info(
            "Action %s: GPU device filter active - allowed devices: %s",
            action_id,
            allowed_gpus
        )

    # For smaller memory requirements, try to fit on a single GPU first
    if required_gpu_memory < 80000:
        logging.debug(
            "Action %s: Required memory %d MB < 80000 MB - attempting single GPU allocation (selecting GPU with most free memory)",
            action_id,
            required_gpu_memory
        )
        try:
            single_gpu = get_single_gpu_with_sufficient_memory_for_action(action_details)
            logging.info(
                "Action %s: Successfully allocated single GPU with most free memory: %s",
                action_id,
                single_gpu
            )
            return single_gpu
        except ValueError as e:
            logging.debug(
                "Action %s: Single GPU allocation failed (%s) - will try multiple GPUs",
                action_id,
                str(e)
            )

    # Multi-GPU allocation: accumulate GPUs until we have enough memory
    logging.info(
        "Action %s: Attempting multi-GPU allocation for %d MB",
        action_id,
        required_gpu_memory
    )

    selected_gpus = []
    total_memory = 0
    for i, mem in enumerate(memory_free_values):
        if not is_allowed_gpu_device(i):
            logging.debug(
                "Action %s: Skipping GPU %d - not in allowed device list",
                action_id,
                i
            )
            continue
        if total_memory >= required_gpu_memory:
            break
        selected_gpus.append(i)
        total_memory += mem
        logging.debug(
            "Action %s: Added GPU %d (%d MB free) - Total: %d MB",
            action_id,
            i,
            mem,
            total_memory
        )

    if total_memory >= required_gpu_memory:
        logging.info(
            "Action %s: Successfully allocated %d GPU(s): %s (Total memory: %d MB >= Required: %d MB)",
            action_id,
            len(selected_gpus),
            selected_gpus,
            total_memory,
            required_gpu_memory
        )
        return selected_gpus

    error_msg = (
        f"Insufficient GPU memory available. "
        f"Required: {required_gpu_memory}MB, "
        f"Available: {total_memory}MB across {len(selected_gpus)} GPU(s)"
    )
    logging.error("Action %s: %s", action_id, error_msg)
    raise ValueError(error_msg)


@log_errors(raise_exception=True, log_error=False)
def get_single_gpu_with_sufficient_memory_for_action(
    action_details: dict,
) -> list:
    """
    Get single GPU with sufficient memory using most-free algorithm.

    Selects the GPU with the MOST free memory that meets the requirements,
    to balance load across GPUs and prevent any single GPU from being overused.

    Args:
        action_details (dict): Action details

    Returns:
        list: List with single GPU index

    Raises:
        ValueError: If no GPU has sufficient memory
    """
    action_id = action_details.get("_id", "unknown")
    required_gpu_memory = get_required_gpu_memory(action_details)

    logging.debug(
        "Action %s: Finding GPU with most free memory for %d MB",
        action_id,
        required_gpu_memory
    )

    command = ["nvidia-smi", "--query-gpu=memory.free", "--format=csv"]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("Failed to get GPU information - nvidia-smi command failed")
        memory_free_info = result.stdout.decode("ascii").strip().split("\n")
    except subprocess.TimeoutExpired:
        logging.error(
            "Action %s: nvidia-smi timed out in single GPU selection",
            action_id
        )
        raise ValueError("Failed to get GPU information - nvidia-smi timed out")
    except FileNotFoundError:
        raise ValueError("nvidia-smi not found - no GPU support available")
    except Exception as e:
        logging.error(
            "Action %s: Error running nvidia-smi: %s",
            action_id,
            e
        )
        raise ValueError(f"Failed to get GPU information: {e}")

    if len(memory_free_info) < 2:
        raise ValueError("No GPU information available from nvidia-smi")

    try:
        memory_free_values = [int(x.split()[0]) for x in memory_free_info[1:] if x.strip()]
    except (ValueError, IndexError) as e:
        raise ValueError(f"Error parsing GPU memory information: {e}")

    if not memory_free_values:
        raise ValueError("No GPU devices found")

    # Most-free algorithm: find GPU with MAXIMUM free memory that meets requirement
    best_fit_gpu = None
    best_fit_memory = 0  # Changed from float("inf") to 0

    for i, mem in enumerate(memory_free_values):
        # Check if GPU is in allowed list
        if not is_allowed_gpu_device(i):
            logging.debug(
                "Action %s: Skipping GPU %d (not in allowed list) - %d MB free",
                action_id,
                i,
                mem
            )
            continue

        # Check if GPU has sufficient memory
        if mem >= required_gpu_memory:
            logging.debug(
                "Action %s: GPU %d is candidate - %d MB free (required: %d MB)",
                action_id,
                i,
                mem,
                required_gpu_memory
            )

            # Most-free: choose GPU with MOST free memory to balance load
            if mem > best_fit_memory:  # Changed from < to >
                best_fit_gpu = i
                best_fit_memory = mem
                logging.debug(
                    "Action %s: GPU %d is new best candidate (most free memory)",
                    action_id,
                    i
                )
        else:
            logging.debug(
                "Action %s: GPU %d insufficient - %d MB free < %d MB required",
                action_id,
                i,
                mem,
                required_gpu_memory
            )

    if best_fit_gpu is not None:
        logging.info(
            "Action %s: Selected GPU %d with most free memory: %d MB free (required: %d MB, available: %d MB)",
            action_id,
            best_fit_gpu,
            best_fit_memory,
            required_gpu_memory,
            best_fit_memory - required_gpu_memory
        )
        return [best_fit_gpu]

    # No suitable GPU found - provide detailed error
    suitable_gpus = [
        f"GPU{i}: {mem}MB (need {required_gpu_memory}MB)"
        for i, mem in enumerate(memory_free_values)
        if is_allowed_gpu_device(i)
    ]

    if not suitable_gpus:
        error_msg = f"No allowed GPUs available (GPUS env filter active)"
    else:
        error_msg = (
            f"No single GPU with sufficient memory. "
            f"Required: {required_gpu_memory}MB. "
            f"Available GPUs: {', '.join(suitable_gpus)}"
        )

    logging.warning("Action %s: %s", action_id, error_msg)
    raise ValueError(error_msg)


@log_errors(default_return="", raise_exception=False)
def get_gpu_config_for_deployment(action_details, is_first_deployment=False):
    """Get GPU configuration for deployment actions.

    For first deployment of a service, attempts to use all GPUs.
    For subsequent deployments, uses standard GPU selection (most free memory).
    Falls back gracefully to standard GPU selection if '--gpus all' is not available.

    Args:
        action_details (dict): Action details containing GPU requirements
        is_first_deployment (bool): Whether this is the first deployment for this service

    Returns:
        str: GPU configuration string ('--gpus all' or '--gpus "device=X"' or '')
    """
    action_id = action_details.get("_id", "unknown")

    # Check if GPU is required
    gpu_required = action_details.get("actionDetails", {}).get("gpuRequired", False)
    if not gpu_required:
        logging.info(
            "Action %s does not require GPU - will run on CPU",
            action_id
        )
        return ""

    # First deployment: try to use all GPUs
    if is_first_deployment:
        logging.info(
            "Action %s: First deployment - attempting to use all GPUs",
            action_id
        )

        try:
            # Check if GPUs are available
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=count", "--format=csv,noheader"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                # GPUs are available, use all of them
                logging.info(
                    "Action %s: Using all GPUs for first deployment",
                    action_id
                )
                return '--gpus all'
            else:
                logging.warning(
                    "Action %s: No GPUs detected via nvidia-smi for first deployment, falling back to standard GPU selection",
                    action_id
                )
        except Exception as e:
            logging.warning(
                "Action %s: Error checking GPU availability (%s), falling back to standard GPU selection",
                action_id,
                str(e)
            )

    # Fall back to standard GPU selection (most free memory)
    # This also handles subsequent deployments
    logging.info(
        "Action %s: Using standard GPU allocation (most free memory)",
        action_id
    )

    required_memory = action_details.get("actionDetails", {}).get(
        "expectedResources", {}
    ).get("gpuMemory", 0)

    try:
        # Get the GPU(s) with most free memory that have sufficient memory
        gpu_indices = get_gpu_with_sufficient_memory_for_action(
            action_details=action_details
        )

        if gpu_indices:
            gpu_str = ",".join(map(str, gpu_indices))
            logging.info(
                "Action %s: Selected GPU device(s): %s (required memory: %d MB)",
                action_id,
                gpu_str,
                required_memory
            )

            # Return Docker GPU configuration
            return f'--gpus "device={gpu_str}"'
        else:
            logging.warning(
                "Action %s: No GPUs with sufficient memory found (required: %d MB)",
                action_id,
                required_memory
            )
            return ""

    except ValueError as e:
        logging.error(
            "Action %s: Error selecting GPU - %s",
            action_id,
            str(e)
        )
        return ""
    except Exception as e:
        logging.error(
            "Action %s: Unexpected error in GPU selection - %s",
            action_id,
            str(e)
        )
        return ""


@log_errors(default_return=(None, None), raise_exception=False)
def get_decrypted_access_key_pair(
    enc_access_key: str,
    enc_secret_key: str,
    encryption_key: str = "",
) -> tuple:
    """
    Get decrypted access key pair.

    Args:
        enc_access_key (str): Encrypted access key
        enc_secret_key (str): Encrypted secret key
        encryption_key (str): Encryption key

    Returns:
        tuple: (access_key, secret_key) strings
    """
    encryption_key = encryption_key or os.environ.get("MATRICE_ENCRYPTION_KEY")
    if not encryption_key:
        logging.warning("Encryption key is not set, Will assume that the keys are not encrypted")
        return enc_access_key, enc_secret_key
    encrypted_access_key = base64.b64decode(enc_access_key)
    encrypted_secret_key = base64.b64decode(enc_secret_key)
    nonce = encrypted_access_key[:12]
    tag = encrypted_access_key[-16:]
    ciphertext = encrypted_access_key[12:-16]
    cipher = Cipher(
        algorithms.AES(encryption_key.encode()),
        modes.GCM(nonce, tag),
        backend=default_backend(),
    )
    decryptor = cipher.decryptor()
    decrypted_access_key = decryptor.update(ciphertext) + decryptor.finalize()
    nonce = encrypted_secret_key[:12]
    tag = encrypted_secret_key[-16:]
    ciphertext = encrypted_secret_key[12:-16]
    cipher = Cipher(
        algorithms.AES(encryption_key.encode()),
        modes.GCM(nonce, tag),
        backend=default_backend(),
    )
    decryptor = cipher.decryptor()
    decrypted_secret_key = decryptor.update(ciphertext) + decryptor.finalize()
    access_key = decrypted_access_key.decode("utf-8", errors="replace")
    secret_key = decrypted_secret_key.decode("utf-8", errors="replace")
    return access_key, secret_key

@log_errors(default_return=(None, None), raise_exception=False)
def get_encrypted_access_key_pair(
    access_key: str,
    secret_key: str,
    encryption_key: str = "",
) -> tuple:
    """
    Get encrypted access key pair.

    Args:
        access_key (str):  access key
        secret_key (str):  secret key
        encryption_key (str): Encryption key

    Returns:
        tuple: (encrypted_access_key, encrypted_secret_key) strings
    """
    encryption_key = encryption_key or os.environ.get("MATRICE_ENCRYPTION_KEY")
    if not encryption_key:
        logging.warning("Encryption key is not set, returning unencrypted keys")
        return access_key, secret_key
    
    # Convert encryption key to bytes
    key = encryption_key.encode()
    
    # Encrypt access key
    nonce = os.urandom(12)
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    encrypted_access_key = encryptor.update(access_key.encode()) + encryptor.finalize()
    encrypted_access_key_with_nonce = nonce + encrypted_access_key + encryptor.tag
    
    # Encrypt secret key
    nonce = os.urandom(12)
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    encrypted_secret_key = encryptor.update(secret_key.encode()) + encryptor.finalize()
    encrypted_secret_key_with_nonce = nonce + encrypted_secret_key + encryptor.tag
    
    # Encode to base64 for storage
    encoded_access_key = base64.b64encode(encrypted_access_key_with_nonce).decode()
    encoded_secret_key = base64.b64encode(encrypted_secret_key_with_nonce).decode()
    
    return encoded_access_key, encoded_secret_key

def _get_private_ip() -> str:
    """
    Get the actual private/LAN IP address using UDP socket trick.
    This works reliably even in Docker, NAT, VPN, etc.
    
    Returns:
        str: Private IP address or None if not available
    """
    try:
        # Use UDP socket to determine which interface would be used for external connection
        # No actual packets are sent
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            private_ip = s.getsockname()[0]
            return private_ip
    except Exception:
        return None


def _public_ip_is_local(public_ip: str) -> bool:
    """
    Check if a public IP address is actually assigned to a local network interface.
    This is true on cloud servers with real public IPs, false behind NAT.
    
    Args:
        public_ip (str): The public IP to check
        
    Returns:
        bool: True if the public IP is on a local interface
    """
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    if addr.address == public_ip:
                        return True
        return False
    except Exception:
        return False


@log_errors(default_return=("localhost", True), raise_exception=False)
def get_best_service_ip_and_network(port: int) -> tuple:
    """
    Determine the best IP address and network configuration for a service.
    
    This function intelligently selects the best IP to bind a service to:
    
    Priority:
    1. Public IP if it's actually on a local interface (cloud servers)
    2. Private/LAN IP (NAT, local network, Docker)
    3. localhost with --net=host (fallback)
    
    Args:
        port (int): Port number for the service
        
    Returns:
        tuple: (ip_address, use_host_network) where:
            - ip_address: The IP address to use (public, private, or localhost)
            - use_host_network: True if should use --net=host, False if should use port mapping
    """
    try:
        # Check if port is available (not already in use)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_sock.bind(("0.0.0.0", port))
                test_sock.listen(1)
                # Port is available - socket closes automatically
        except OSError as e:
            logging.warning(f"Port {port} is already in use or cannot be bound: {e}, will use --net=host")
            return "localhost", True
        
        # Get the actual private/LAN IP
        private_ip = _get_private_ip()
        if private_ip:
            logging.info(f"Determined private/LAN IP: {private_ip}")
        else:
            logging.debug("Could not determine private IP")
        
        # Try to get public IP from external service
        public_ip = None
        try:
            public_ip = urllib.request.urlopen("https://ident.me", timeout=10).read().decode("utf8").strip()
            # Validate it's a proper IP address
            socket.inet_aton(public_ip)
            logging.info(f"Determined external/public IP: {public_ip}")
        except Exception as e:
            logging.debug(f"Could not determine public IP: {e}")
        
        # Decision logic: Choose the best IP
        
        # 1. If public IP is on a local interface, use it (cloud server with real public IP)
        if public_ip and _public_ip_is_local(public_ip):
            logging.info(f"Public IP {public_ip} is on local interface, using it for port {port}")
            return public_ip, False
        
        # 2. If we have a valid private IP, use it (most common case: NAT, LAN, Docker)
        if private_ip and not private_ip.startswith("127."):
            logging.info(f"Using private/LAN IP {private_ip} for port {port}")
            return private_ip, False
        
        # 3. Fall back to localhost with --net=host
        logging.info(f"No suitable IP found, using localhost with --net=host for port {port}")
        return "localhost", True
        
    except Exception as e:
        logging.warning(f"Error determining best IP for port {port}: {e}, falling back to localhost")
        return "localhost", True
