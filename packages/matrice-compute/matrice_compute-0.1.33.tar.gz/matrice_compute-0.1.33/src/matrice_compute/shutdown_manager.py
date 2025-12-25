"""Module providing shutdown_manager functionality."""

import logging
import time
import os
import sys
import platform
import subprocess
import signal
from typing import Optional, Tuple
from matrice_common.utils import log_errors
from matrice_compute.scaling import Scaling


class ShutdownManager:
    """Class for managing compute instance shutdown."""

    def __init__(self, scaling: Scaling) -> None:
        """
        Initialize ShutdownManager.

        Args:
            scaling (Scaling): Scaling instance to manage shutdown.
        """
        self.scaling = scaling
        self.launch_time: float = time.time()
        self.last_no_queued_time: Optional[float] = None
        self.shutdown_threshold: int = 500  # Idle time threshold in seconds
        self.launch_duration: int = 1  # Launch duration in minutes
        self.instance_source: str = "auto"
        self.encryption_key: Optional[str] = None
        self.reserved_instance: Optional[bool] = None
        self.shutdown_attempts: int = 0
        self.max_shutdown_attempts: int = 3
        self.force_shutdown_attempts: int = 0
        self.max_force_shutdown_attempts: int = 2
        self.launch_duration_seconds: int = self.launch_duration * 60  # Convert minutes to seconds
        self._load_shutdown_configuration()

    @log_errors(raise_exception=False, log_error=True)
    def _load_shutdown_configuration(self) -> None:
        """
        Load shutdown configuration from AWS secrets and initialize parameters.

        This method retrieves shutdown configuration details from the scaling service
        and updates the instance attributes accordingly.
        """
        response, error, message = self.scaling.get_shutdown_details()
        if error is None:
            self.shutdown_threshold = response.get("shutdownThreshold", 500)
            self.launch_duration = response.get("launchDuration", 1)
            self.instance_source = response.get("instanceSource", "auto")
            self.encryption_key = response.get("encryptionKey")
        self.launch_duration_seconds = self.launch_duration * 60  # Convert minutes to seconds
        self.reserved_instance = self.instance_source == "reserved"
        logging.info(
            "Loaded shutdown configuration: threshold=%s, duration=%s, source=%s, reserved=%s",
            self.shutdown_threshold,
            self.launch_duration,
            self.instance_source,
            self.reserved_instance,
        )

    def _check_root(self) -> bool:
        """
        Check if the current process has root privileges.

        Returns:
            bool: True if the process has root privileges, False otherwise.
        """
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            logging.error("Shutdown requires root privileges.")
            return False
        return True

    def _execute_shutdown_command(self) -> bool:
        """
        Execute system shutdown command with multiple fallbacks.

        This method attempts to shut down the system using various commands
        depending on the operating system.

        Returns:
            bool: True if any shutdown command succeeded, False otherwise.
        """
        self._check_root()
        system = platform.system().lower()
        
        # Define shutdown commands in order of preference (most graceful first)
        shutdown_commands = []
        
        if system == "linux":
            shutdown_commands = [
                ["shutdown", "now"],  # Standard Linux shutdown
                ["systemctl", "poweroff"],  # Systemd poweroff
                ["systemctl", "poweroff", "--force"],  # Force systemd poweroff
                ["halt", "-f"],  # Force halt
                ["poweroff", "-f"],  # Force poweroff
                ["init", "0"],  # Init level 0 (shutdown)
                ["telinit", "0"],  # Alternative init command
            ]
        elif system == "windows":
            shutdown_commands = [
                ["shutdown", "/s", "/t", "0"],  # Windows shutdown
                ["shutdown", "/s", "/f", "/t", "0"],  # Windows force shutdown
                ["shutdown", "/p"],  # Windows immediate poweroff
            ]
        elif system == "darwin":  # macOS
            shutdown_commands = [
                ["shutdown", "-h", "now"],  # macOS shutdown
                ["halt"],  # macOS halt
                ["sudo", "shutdown", "-h", "now"],  # Sudo shutdown
            ]
        else:
            # Generic Unix-like fallbacks
            shutdown_commands = [
                ["shutdown", "-h", "now"],
                ["halt"],
                ["poweroff"],
                ["init", "0"],
            ]
        
        # Try each command in sequence
        for cmd in shutdown_commands:
            try:
                logging.info("Attempting shutdown with command: %s", " ".join(cmd))
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    check=False
                )
                
                if result.returncode == 0:
                    logging.info("Shutdown command succeeded: %s", " ".join(cmd))
                    return True
                else:
                    logging.warning(
                        "Shutdown command failed with return code %d: %s. STDERR: %s", 
                        result.returncode, 
                        " ".join(cmd),
                        result.stderr
                    )
            except subprocess.TimeoutExpired:
                logging.warning("Shutdown command timed out: %s", " ".join(cmd))
            except FileNotFoundError:
                logging.warning("Shutdown command not found: %s", " ".join(cmd))
            except Exception as e:
                logging.warning("Shutdown command failed: %s. Error: %s", " ".join(cmd), str(e))
        
        # If all standard commands failed, try more aggressive methods
        return self._try_aggressive_shutdown()

    def _try_aggressive_shutdown(self) -> bool:
        """
        Try more aggressive shutdown methods when standard commands fail.

        Returns:
            bool: True if any aggressive shutdown method succeeded, False otherwise.
        """
        logging.warning("Standard shutdown commands failed, trying aggressive methods")
        try:
            system = platform.system().lower()
            if system == "linux":
                try:
                    subprocess.run("echo 1 > /proc/sys/kernel/sysrq", shell=True, check=False, timeout=5)
                except Exception:
                    pass

                aggressive_commands = [
                    "sync",
                    "echo 4 > /proc/acpi/sleep",
                    "echo s > /proc/sysrq-trigger",
                    "echo u > /proc/sysrq-trigger",
                    "echo o > /proc/sysrq-trigger",
                    "echo b > /proc/sysrq-trigger",
                ]
                for cmd in aggressive_commands:
                    try:
                        logging.info("Trying aggressive shutdown: %s", cmd)
                        result = subprocess.run(cmd, shell=True, check=False, timeout=10)
                        if result.returncode == 0:
                            logging.info("Aggressive shutdown command succeeded")
                            time.sleep(2)
                            return True
                    except Exception as e:
                        logging.info("Aggressive command failed: %s", str(e))
        except Exception as e:
            logging.error("Error in aggressive shutdown methods: %s", str(e))
        return False
    

    @log_errors(raise_exception=True, log_error=True)
    def do_cleanup_and_shutdown(self) -> bool:
        """Clean up resources and shut down the instance.
        
        This method attempts a coordinated shutdown with multiple fallback strategies:
        1. API call to notify the scaling service
        2. Graceful OS shutdown command
        3. Aggressive shutdown methods if needed
        4. Emergency forced shutdown as last resort
        
        Returns:
            bool: True if shutdown was initiated successfully, False otherwise
        """
        max_retries = self.max_shutdown_attempts
        
        for attempt in range(1, max_retries + 1):
            try:
                logging.info("Shutdown attempt %d of %d", attempt, max_retries)
                
                # Step 1: Notify scaling service of shutdown
                logging.info("Notifying scaling service of instance shutdown")
                try:
                    response = self.scaling.stop_instance()
                    
                    # Handle case where stop_instance returns None or unexpected format
                    if response is None:
                        result, error, message = None, "API returned None", "No response from stop_instance API"
                    elif isinstance(response, tuple) and len(response) == 3:
                        result, error, message = response
                    else:
                        result, error, message = None, "Invalid response format", f"Unexpected response format: {response}"
                        
                except Exception as api_error:
                    result, error, message = None, str(api_error), "Exception during API call"
                
                if error:
                    logging.error("Failed to notify scaling service (attempt %d): %s", attempt, error)
                    if attempt < max_retries:
                        logging.info("Retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                    else:
                        logging.warning("Proceeding with shutdown despite API notification failure")
                else:
                    logging.info("Scaling service notified successfully: %s", message)
                
                # Step 2: Attempt graceful system shutdown
                logging.info("Initiating graceful system shutdown")
                shutdown_success = self._execute_shutdown_command()
                
                if shutdown_success:
                    logging.info("Graceful shutdown command executed successfully")
                    # Give the system time to process the shutdown
                    time.sleep(10)
                    # If we reach here, graceful shutdown may have failed
                    logging.warning("System did not shut down gracefully, trying aggressive methods")
                
                # Step 3: Try aggressive shutdown methods
                logging.warning("Attempting aggressive shutdown methods")
                aggressive_success = self._try_aggressive_shutdown()
                
                if aggressive_success:
                    logging.info("Aggressive shutdown initiated")
                    time.sleep(5)
                
                return True
                
            except Exception as e:
                logging.error("Critical error during shutdown attempt %d: %s", attempt, str(e)) 
        return False

    @log_errors(raise_exception=False, log_error=True)
    def handle_shutdown(self, tasks_running: bool) -> None:
        """Check idle time and trigger shutdown if threshold is exceeded.

        Args:
            tasks_running: Boolean indicating if there are running tasks
        """
        # CRITICAL: Check if this is a reserved instance that should not be shut down
        # if self.reserved_instance:
        #     logging.info("Reserved instance detected, skipping shutdown check")
        #     return

        # Update idle time tracking
        if tasks_running:
            self.last_no_queued_time = None
            logging.info("Tasks are running, resetting idle timer")
        elif self.last_no_queued_time is None:
            self.last_no_queued_time = time.time()
            logging.info("No tasks running, starting idle timer")

        if self.last_no_queued_time is not None:
            idle_time = time.time() - self.last_no_queued_time
            launch_time_passed = (time.time() - self.launch_time) > self.launch_duration_seconds

            # Log current status
            logging.info(
                "Time since last action: %s seconds. Time left to shutdown: %s seconds.",
                idle_time,
                max(0, self.shutdown_threshold - idle_time),
            )

            # Check if we should shut down
            if idle_time <= self.shutdown_threshold:
                return

            if not launch_time_passed:
                logging.info(
                "Instance not shutting down yet. Launch duration: %s seconds, elapsed: %s seconds",
                    self.launch_duration_seconds,
                    time.time() - self.launch_time,
                )
                return

            logging.info(
                "Idle time %s seconds exceeded threshold %s seconds. Shutting down.",
                idle_time,
                self.shutdown_threshold
            )

            self.do_cleanup_and_shutdown()
