"""
This module contains classes for tracking machine and action resources.
"""

import os
import subprocess
import logging
import threading
import json
from datetime import datetime, timezone
import psutil
import docker
from typing import List, Tuple, Dict, Optional
from matrice_compute.instance_utils import (
    has_gpu,
    get_gpu_info,
    calculate_time_difference,
)
from matrice_compute.scaling import Scaling
from matrice_common.utils import log_errors


class ResourcesTracker:
    """Tracks machine and container resources."""

    def __init__(self) -> None:
        """
        Initialize ResourcesTracker.
        """
        pass

    @log_errors(default_return=(0, 0), raise_exception=False)
    def get_container_cpu_and_memory(self, container: docker.models.containers.Container) -> Tuple[float, float]:
        """
        Get CPU and memory usage for a container.

        Args:
            container (docker.models.containers.Container): Docker container instance.

        Returns:
            Tuple[float, float]: CPU utilization percentage and memory utilization percentage.
        """
        stats = container.stats(stream=False)
        if stats:
            cpu_utilization = 0
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = stats["cpu_stats"].get("system_cpu_usage", 0) - stats[
                "precpu_stats"
            ].get("system_cpu_usage", 0)
            if system_delta > 0:
                cpu_utilization = cpu_delta / system_delta * 100.0
            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 1)
            memory_utilization = memory_usage / memory_limit * 100.0
            return cpu_utilization, memory_utilization
        return 0, 0

    @log_errors(default_return=(0, 0), raise_exception=False, log_error=False)
    def get_container_cpu_and_memory_with_container_id(self, container_id: str) -> Tuple[float, float]:
        """
        Get CPU and memory usage for a specific container by its ID.

        Args:
            container_id (str): ID of the Docker container.

        Returns:
            Tuple[float, float]: CPU utilization percentage and memory usage in MB.
        """
        try:
            stats_result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "{{.ID}}: {{.CPUPerc}} CPU, {{.MemUsage}} RAM",
                    container_id,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if stats_result.returncode != 0:
                logging.debug("docker stats command failed for container %s", container_id)
                return 0, 0
            stats = stats_result.stdout.strip().split(": ")[1].split(", ")
            cpu_usage = float(stats[0].replace("% CPU", "").strip())
            memory_usage = stats[1].split(" / ")[0]
            mem_value, mem_unit = memory_usage[:-3], memory_usage[-3:]
            if mem_unit == "KiB":
                memory_usage_mb = float(mem_value) / 1024
            elif mem_unit == "MiB":
                memory_usage_mb = float(mem_value)
            elif mem_unit == "GiB":
                memory_usage_mb = float(mem_value) * 1024
            else:
                memory_usage_mb = float(mem_value)
            return cpu_usage, memory_usage_mb
        except subprocess.TimeoutExpired:
            logging.debug("docker stats command timed out for container %s", container_id)
            return 0, 0
        except (ValueError, IndexError) as e:
            logging.debug("Error parsing docker stats for container %s: %s", container_id, e)
            return 0, 0
        except Exception as e:
            logging.debug("Unexpected error getting container stats for %s: %s", container_id, e)
            return 0, 0

    @log_errors(default_return=(0, 0), raise_exception=False, log_error=False)
    def get_container_gpu_info(self, container_id: str) -> Tuple[float, int]:
        """
        Get GPU usage for a specific container.

        Args:
            container_id (str): ID of the Docker container.

        Returns:
            Tuple[float, int]: GPU utilization percentage and GPU memory usage in MB.
        """
        container_pid = self.get_pid_id_by_container_id(container_id)
        gpu_util = self.get_container_gpu_usage(container_pid)
        gpu_mem_used = self.get_container_gpu_memory_usage(container_pid)
        return gpu_util, gpu_mem_used

    @log_errors(default_return="", raise_exception=False, log_error=False)
    def get_pid_id_by_container_id(self, container_id: str) -> str:
        """
        Get PID for a container ID.

        Args:
            container_id (str): ID of the Docker container.

        Returns:
            str: PID of the container.
        """
        try:
            pid_result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{.State.Pid}}",
                    container_id,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if pid_result.returncode != 0:
                logging.debug("docker inspect command failed for container %s", container_id)
                return ""
            container_pid = pid_result.stdout.strip()
            return container_pid
        except subprocess.TimeoutExpired:
            logging.debug("docker inspect command timed out for container %s", container_id)
            return ""
        except Exception as e:
            logging.debug("Error getting PID for container %s: %s", container_id, e)
            return ""

    @log_errors(default_return=0, raise_exception=False, log_error=False)
    def get_container_gpu_usage(self, container_pid: str) -> float:
        """
        Get GPU usage for a container PID.

        Args:
            container_pid (str): PID of the Docker container.

        Returns:
            float: GPU utilization percentage.
        """
        if not has_gpu():
            return 0
        gpu_util = 0
        try:
            result = subprocess.run(
                ["nvidia-smi", "pmon", "-c", "1"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if result.returncode != 0:
                logging.debug("nvidia-smi pmon command failed in get_container_gpu_usage")
                return 0
            pmon_output = result.stdout.strip().split("\n")
            for line in pmon_output[2:]:
                parts = line.split()
                if len(parts) >= 8:
                    pid = parts[1]
                    gpu_usage = parts[3]
                    if pid == str(container_pid):
                        gpu_util += float(gpu_usage) if gpu_usage != "-" else 0
        except subprocess.TimeoutExpired:
            logging.debug("nvidia-smi pmon command timed out after 5 seconds in get_container_gpu_usage")
            return 0
        except (ValueError, IndexError) as e:
            logging.debug("Error parsing GPU usage info: %s", e)
            return 0
        except FileNotFoundError:
            logging.debug("nvidia-smi not found on this system")
            return 0
        except Exception as e:
            logging.debug("Unexpected error in get_container_gpu_usage: %s", e)
            return 0
        return gpu_util

    @log_errors(default_return=0, raise_exception=False, log_error=False)
    def get_container_gpu_memory_usage(self, container_pid: str) -> int:
        """
        Get GPU memory usage for a container PID.

        Args:
            container_pid (str): PID of the Docker container.

        Returns:
            int: GPU memory usage in MB.
        """
        if not has_gpu():
            return 0
        cmd = [
            "nvidia-smi",
            "--query-compute-apps=pid,used_memory",
            "--format=csv,noheader,nounits",
        ]
        total_memory = 0
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=5,
            )
            if result.returncode != 0:
                logging.debug("nvidia-smi command failed in get_container_gpu_memory_usage")
                return 0
            for line in result.stdout.splitlines():
                parts = line.strip().split(", ")
                if len(parts) == 2:
                    process_pid, used_memory = parts
                    if process_pid == str(container_pid):
                        total_memory += int(used_memory)
        except subprocess.TimeoutExpired:
            logging.debug("nvidia-smi command timed out after 5 seconds in get_container_gpu_memory_usage")
            return 0
        except (ValueError, IndexError) as e:
            logging.debug("Error parsing GPU memory usage info: %s", e)
            return 0
        except FileNotFoundError:
            logging.debug("nvidia-smi not found on this system")
            return 0
        except Exception as e:
            logging.debug("Unexpected error in get_container_gpu_memory_usage: %s", e)
            return 0
        return total_memory

    @log_errors(default_return=(0, 0, 0, 0), raise_exception=False, log_error=True)
    def get_available_resources(self) -> Tuple[float, float, int, float]:
        """
        Get available machine resources.

        Returns:
            Tuple[float, float, int, float]: Available memory in GB, available CPU percentage,
            free GPU memory in MB, and GPU utilization percentage.
        """
        available_memory = psutil.virtual_memory().available / 1024**3
        available_cpu = 100 - psutil.cpu_percent(1)
        gpu_memory_free, gpu_utilization = self._get_gpu_resources()
        return available_memory, available_cpu, gpu_memory_free, gpu_utilization

    @log_errors(default_return=(0, 0.0), raise_exception=False, log_error=False)
    def _get_gpu_resources(self) -> Tuple[int, float]:
        """
        Get available GPU resources.

        Returns:
            Tuple[int, float]: Free GPU memory in MB and GPU utilization percentage.
        """
        gpu_memory_free = 0
        gpu_utilization = 0.0
        if not has_gpu():
            return gpu_memory_free, gpu_utilization

        try:
            result = subprocess.run(
                ["nvidia-smi"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            if result.returncode != 0:
                logging.debug("nvidia-smi command failed in _get_gpu_resources")
                return 0, 0.0
        except subprocess.TimeoutExpired:
            logging.debug("nvidia-smi command timed out after 5 seconds in _get_gpu_resources")
            return 0, 0.0
        except FileNotFoundError:
            logging.debug("nvidia-smi not found on this system")
            return 0, 0.0
        except Exception as e:
            logging.debug("Error running nvidia-smi in _get_gpu_resources: %s", e)
            return 0, 0.0
        
        info_list = get_gpu_info()
        if not info_list:
            return 0, 0.0
        
        try:
            for info in info_list:
                info_split = info.split(", ")
                if len(info_split) >= 6:
                    gpu_memory_free += int(info_split[5])
                    gpu_utilization += float(info_split[2])
            gpu_utilization /= len(info_list) if info_list else 1
        except (ValueError, IndexError) as e:
            logging.debug("Error parsing GPU resources: %s", e)
            return 0, 0.0

        return gpu_memory_free, gpu_utilization


class ActionsResourcesTracker:
    """Tracks Docker container action resources"""

    def __init__(self, scaling: Scaling):
        """Initialize ActionsResourcesTracker"""
        self.scaling = scaling
        self.max_actions_usage = {}
        self.resources_tracker = ResourcesTracker()
        self.client = docker.from_env()
        self.logged_stopped_containers = []

    @log_errors(raise_exception=False, log_error=True)
    def update_actions_resources(self) -> None:
        """Process both running and exited containers.
        
        Note: Does not remove containers to keep logs. Only tracks resource usage.
        """
        exited_containers = self.client.containers.list(
            filters={"status": "exited"},
            all=True,
        )
        running_containers = self.client.containers.list(filters={"status": "running"})
        if exited_containers:
            for container in exited_containers:
                try:
                    if container.id in self.logged_stopped_containers:
                        continue
                    self._update_container_action_status(container, "completed")
                    self.logged_stopped_containers.append(container.id)
                    # COMMENTED OUT: Do not remove containers to keep logs
                    # container.remove()
                except Exception as err:
                    logging.error(
                        "Error processing exited container %s: %s",
                        container.id,
                        str(err),
                    )
        if running_containers:
            for container in running_containers:
                try:
                    self._update_container_action_status(container, "running")
                except Exception as err:
                    logging.error(
                        "Error processing running container %s: %s",
                        container.id,
                        str(err),
                    )

    @log_errors(default_return=[], raise_exception=False)
    def get_sub_containers_by_label(self, label_key: str, label_value: str) -> list:
        """Get running containers with specified label key and value"""
        containers = self.client.containers.list(
            filters={
                "label": [f"{label_key}={label_value}"],
                "status": "running",
            }
        )
        return containers

    @log_errors(raise_exception=False, log_error=True)
    def _update_container_action_status(self, container, status: str) -> None:
        """Update action status for a specific container"""
        inspect_data = self.client.api.inspect_container(container.id)
        start_time = inspect_data["State"]["StartedAt"]
        finish_time = (
            inspect_data["State"]["FinishedAt"]
            if status == "completed"
            else datetime.now(timezone.utc).isoformat()
        )

        def remove_quotation_marks(args):
            """Remove quotes from container args"""
            new_args = []
            for arg in args:
                new_args.extend(x.replace('"', "").replace("'", "") for x in arg.split(" "))
            return new_args

        def is_valid_objectid(s: str) -> bool:
            """Check if string is a valid MongoDB ObjectId (24 hex characters)"""
            s = s.strip()
            return len(s) == 24 and all(c in '0123456789abcdefABCDEF' for c in s)
        
        valid_objectids = [arg for arg in remove_quotation_marks(inspect_data["Args"]) if is_valid_objectid(arg)]
        action_record_id = valid_objectids[-1] if valid_objectids else None
        if not action_record_id:
            logging.debug("No valid action_id found for the container. Container ID: %s, Args: %s", container.id, inspect_data["Args"])
        duration = calculate_time_difference(start_time, finish_time)
        (
            current_gpu_utilization,
            current_gpu_memory,
            current_cpu_utilization,
            current_memory_utilization,
        ) = self.get_current_action_usage(container, status)
        sub_containers = self.get_sub_containers_by_label("action_id", action_record_id)
        for sub_container in sub_containers:
            if sub_container.id in self.logged_stopped_containers:
                continue
            (
                sub_container_gpu_utilization,
                sub_container_gpu_memory,
                sub_container_cpu_utilization,
                sub_container_memory_utilization,
            ) = self.get_current_action_usage(sub_container, status)
            current_gpu_utilization += sub_container_gpu_utilization
            current_gpu_memory += sub_container_gpu_memory
            current_cpu_utilization += sub_container_cpu_utilization
            current_memory_utilization += sub_container_memory_utilization
            # COMMENTED OUT: Do not stop/remove sub-containers to keep logs
            if status == "completed":
                try:
                    sub_container.stop()
                    self.logged_stopped_containers.append(sub_container.id)
            #         sub_container.remove(force=True)
                except Exception as err:
                    logging.error(
                        "Error removing sub-container %s: %s",
                        sub_container.id,
                        str(err),
                    )
        (
            max_gpu_utilization,
            max_gpu_memory,
            max_cpu_utilization,
            max_memory_utilization,
        ) = self.update_max_action_usage(
            action_record_id,
            current_gpu_utilization,
            current_gpu_memory,
            current_cpu_utilization,
            current_memory_utilization,
        )
        logging.info(
            "Updating action status: service_provider=%s, action_id=%s, running=%s, status=%s, duration=%s, start=%s, gpu_util=%.2f%%, cpu_util=%.2f%%, gpu_mem=%dMB, mem_util=%.2f%%, created=%s, updated=%s",
            os.environ["SERVICE_PROVIDER"],
            action_record_id,
            status == "running",
            status,
            duration,
            start_time,
            max_gpu_utilization,
            max_cpu_utilization,
            max_gpu_memory,
            max_memory_utilization,
            start_time,
            finish_time,
        )
        self.scaling.update_action_status(
            service_provider=os.environ["SERVICE_PROVIDER"],
            action_record_id=action_record_id,
            isRunning=status == "running",
            status=status,
            action_duration=duration,
            docker_start_time=start_time,
            gpuUtilisation=max_gpu_utilization,
            cpuUtilisation=max_cpu_utilization,
            gpuMemoryUsed=max_gpu_memory,
            memoryUtilisation=max_memory_utilization,
            createdAt=start_time,
            updatedAt=finish_time,
        )

    @log_errors(default_return=(0, 0, 0, 0), raise_exception=False)
    def get_current_action_usage(self, container, status: str) -> Tuple[float, int, float, float]:
        """Get current resource usage for a container"""
        current_gpu_utilization = 0
        current_gpu_memory = 0
        current_cpu_utilization = 0
        current_memory_utilization = 0
        if status == "running":
            try:
                (
                    current_cpu_utilization,
                    current_memory_utilization,
                ) = self.resources_tracker.get_container_cpu_and_memory(container)
                (
                    current_gpu_utilization,
                    current_gpu_memory,
                ) = self.resources_tracker.get_container_gpu_info(container_id=container.id)
            except Exception as err:
                logging.error(
                    "Error getting container usage metrics: %s",
                    str(err),
                )
        return (
            current_gpu_utilization,
            current_gpu_memory,
            current_cpu_utilization,
            current_memory_utilization,
        )

    @log_errors(default_return=(0, 0, 0, 0), raise_exception=False, log_error=True)
    def update_max_action_usage(
        self,
        action_record_id: str,
        current_gpu_utilization: float,
        current_gpu_memory: int,
        current_cpu_utilization: float,
        current_memory_utilization: float,
    ) -> Tuple[float, int, float, float]:
        
        """Update and return maximum resource usage values for an action"""
        if action_record_id not in self.max_actions_usage:
            self.max_actions_usage[action_record_id] = {
                "gpu_utilization": 0,
                "gpu_memory": 0,
                "cpu_utilization": 0,
                "memory_utilization": 0,
            }
        current_values = {
            "gpu_utilization": current_gpu_utilization or 0,
            "gpu_memory": current_gpu_memory or 0,
            "cpu_utilization": current_cpu_utilization or 0,
            "memory_utilization": current_memory_utilization or 0,
        }
        for key in current_values:
            self.max_actions_usage[action_record_id][key] = max(
                current_values[key],
                self.max_actions_usage[action_record_id][key],
            )
        return (
            self.max_actions_usage[action_record_id]["gpu_utilization"],
            self.max_actions_usage[action_record_id]["gpu_memory"],
            self.max_actions_usage[action_record_id]["cpu_utilization"],
            self.max_actions_usage[action_record_id]["memory_utilization"],
        )


class MachineResourcesTracker:
    """Tracks machine-level resources like CPU, memory and GPU"""

    def __init__(self, scaling: Scaling):
        """Initialize MachineResourcesTracker"""
        self.scaling = scaling
        self.resources_tracker = ResourcesTracker()

    @log_errors(raise_exception=False, log_error=True)
    def update_available_resources(self):
        """Update available machine resources"""
        (
            available_memory,
            available_cpu,
            gpu_memory_free,
            gpu_utilization,
        ) = self.resources_tracker.get_available_resources()
        _, err, _ = self.scaling.update_available_resources(
            availableCPU=available_cpu,
            availableMemory=available_memory,
            availableGPU=100 - gpu_utilization,
            availableGPUMemory=gpu_memory_free,
        )
        if err is not None:
            logging.error(
                "Error in updating available resources: %s",
                err,
            )


class KafkaResourceMonitor:
    """
    Monitors system resources and publishes them to Kafka in a separate thread.
    This class provides thread-safe start/stop operations for resource monitoring.
    """

    def __init__(
        self,
        instance_id: Optional[str] = None,
        kafka_bootstrap: Optional[str] = None,
        interval_seconds: int = 60,
    ):
        """
        Initialize KafkaResourceMonitor.

        Args:
            instance_id: Instance identifier for Kafka topic. Defaults to INSTANCE_ID env var.
            kafka_bootstrap: Kafka bootstrap servers. Required - should be obtained from Scaling.get_kafka_bootstrap_servers().
            interval_seconds: Interval between resource checks in seconds. Defaults to 60.
        """
        self.instance_id = instance_id or os.getenv("INSTANCE_ID")
        if not self.instance_id:
            raise ValueError("instance_id must be provided or INSTANCE_ID env var must be set")

        if not kafka_bootstrap:
            raise ValueError("kafka_bootstrap must be provided - use Scaling.get_kafka_bootstrap_servers() to get internal Kafka config")

        self.kafka_bootstrap = kafka_bootstrap
        self.interval_seconds = interval_seconds
        self.topic_name = "compute_instance_resource_utilization"

        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._producer = None
        self._is_running = False

    @staticmethod
    def get_all_gpu_memory() -> Dict[int, tuple]:
        """
        Get GPU memory usage and total for all GPUs.

        Returns:
            Dict[int, tuple]: Dictionary mapping GPU ID to (used_gb, total_gb).
                             Returns empty dict if nvidia-smi is not available.
        """
        gpu_usage = {}

        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=index,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ]
            result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=5)
            lines = result.decode().strip().split("\n")

            for line in lines:
                gpu_id_str, mem_used_mb_str, mem_total_mb_str = line.split(",")
                gpu_id = int(gpu_id_str.strip())
                mem_used_gb = int(mem_used_mb_str.strip()) / 1024  # MB → GB
                mem_total_gb = int(mem_total_mb_str.strip()) / 1024  # MB → GB
                gpu_usage[gpu_id] = (round(mem_used_gb, 2), round(mem_total_gb, 2))

        except Exception as e:
            logging.debug("Failed to get GPU memory info: %s", e)
            return {}

        return gpu_usage

    @staticmethod
    def get_all_storage_info() -> Dict[str, float]:
        """
        Get free storage space for all mounted drives.

        Returns:
            Dict[str, float]: Dictionary mapping mount point to free storage space in GB.
        """
        storage_info = {}

        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    # Get usage statistics for this partition
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Convert bytes to GB
                    free_gb = usage.free / (1024 ** 3)
                    
                    storage_info[partition.mountpoint] = round(free_gb, 2)
                    
                except PermissionError:
                    # Skip drives that we can't access (common on Windows)
                    logging.debug("Permission denied accessing %s", partition.mountpoint)
                    continue
                except Exception as e:
                    logging.debug("Error getting storage info for %s: %s", partition.mountpoint, e)
                    continue
                    
        except Exception as e:
            logging.debug("Failed to get storage info: %s", e)
            return {}

        return storage_info

    def get_stats(self) -> Tuple[float, int, float, float, Dict[int, tuple], Dict[str, float]]:
        """
        Collect current system resource statistics.

        Returns:
            Tuple[float, int, float, float, Dict[int, tuple], Dict[str, float]]: 
            CPU usage %, CPU cores, RAM total GB, RAM used GB, GPU memory dict (used, total), Free storage dict
        """
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_cores = psutil.cpu_count(logical=True)  # Total logical CPU cores

        mem = psutil.virtual_memory()
        ram_total = mem.total / (1024 ** 3)
        ram_used = mem.used / (1024 ** 3)

        gpu_usage = self.get_all_gpu_memory()
        storage_info = self.get_all_storage_info()

        return cpu_usage, cpu_cores, ram_total, ram_used, gpu_usage, storage_info

    def _monitor_worker(self):
        """
        Worker function that runs in a separate thread to monitor and publish resources.
        """
        try:
            from kafka import KafkaProducer

            self._producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
            )
            logging.info("Kafka resource monitor started. Publishing to topic: %s", self.topic_name)

        except ImportError:
            logging.error("kafka-python not installed. Install with: pip install kafka-python")
            return
        except Exception as e:
            logging.error("Failed to initialize Kafka producer: %s", e)
            return

        while not self._stop_event.is_set():
            try:
                cpu, cpu_cores, total, used, gpus, storage = self.get_stats()

                # Format GPU info for output: {0: {"used_gb": x, "total_gb": y}, ...}
                gpu_memory_gb = {k: {"used_gb": v[0], "total_gb": v[1]} for k, v in gpus.items()}
                payload = {
                    "instance_id": self.instance_id,
                    "cpu_usage_percent": round(cpu, 2),
                    "cpu_cores": cpu_cores,
                    "ram_total_gb": round(total, 2),
                    "ram_used_gb": round(used, 2),
                    "gpu_memory_gb": gpu_memory_gb,  # dict: {0: {used_gb, total_gb}, ...}
                    "free_storage_gb": storage,  # dict: {"/": 50.5, "C:": 123.4}
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                self._producer.send(self.topic_name, payload)
                self._producer.flush()

                logging.debug("Published resource stats: %s", payload)

            except Exception as e:
                logging.error("Error in resource monitor loop: %s", e)

            # Wait for interval or until stop event is set
            if self._stop_event.wait(self.interval_seconds):
                break

        # Cleanup
        if self._producer:
            try:
                self._producer.close()
            except Exception as e:
                logging.debug("Error closing Kafka producer: %s", e)

        logging.info("Kafka resource monitor stopped.")

    @log_errors(raise_exception=False, log_error=True)
    def start(self):
        """
        Start the resource monitoring thread.

        Returns:
            bool: True if started successfully, False otherwise.
        """
        if self._is_running:
            logging.warning("Kafka resource monitor is already running.")
            return False

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_worker,
            daemon=True,
            name="KafkaResourceMonitor"
        )
        self._monitor_thread.start()
        self._is_running = True

        logging.info("Started Kafka resource monitor thread.")
        return True

    @log_errors(raise_exception=False, log_error=True)
    def stop(self, timeout: int = 10):
        """
        Stop the resource monitoring thread gracefully.

        Args:
            timeout: Maximum time to wait for thread to stop in seconds.

        Returns:
            bool: True if stopped successfully, False otherwise.
        """
        if not self._is_running:
            logging.warning("Kafka resource monitor is not running.")
            return False

        logging.info("Stopping Kafka resource monitor...")
        self._stop_event.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=timeout)

            if self._monitor_thread.is_alive():
                logging.error("Kafka resource monitor thread did not stop within timeout.")
                return False

        self._is_running = False
        logging.info("Kafka resource monitor stopped successfully.")
        return True

    def is_running(self) -> bool:
        """
        Check if the resource monitor is currently running.

        Returns:
            bool: True if running, False otherwise.
        """
        return self._is_running

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
