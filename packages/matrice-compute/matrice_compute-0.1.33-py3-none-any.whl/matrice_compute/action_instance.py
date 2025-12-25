"""Module providing action_instance functionality."""

import logging
import os
import shlex
import subprocess
import threading
import time
import signal
import urllib.request
from matrice_compute.instance_utils import (
    get_gpu_with_sufficient_memory_for_action,
    get_gpu_config_for_deployment,
    get_decrypted_access_key_pair,
    get_max_file_system,
    get_best_service_ip_and_network,
)
from matrice_compute.task_utils import (
    setup_workspace_and_run_task,
)
from matrice_compute.scaling import (
    Scaling,
)
from matrice_common.utils import log_errors


class ActionInstance:
    """Base class for tasks that run in Action containers."""

    # Class-level dictionary to track deployed services and their ports
    # Key: _idService, Value: {"triton_ports": "port1,port2,port3", "is_first": False}
    _deployed_services = {}

    def __init__(self, scaling: Scaling, action_info: dict):
        """Initialize an action instance.

        Args:
            scaling (Scaling): Scaling service instance
            action_info (dict): Action information dictionary
        """
        self.scaling = scaling
        self.process: subprocess.Popen | None = None
        self.stop_thread = False
        self.log_thread: threading.Thread | None = None
        self.log_path: str | None = None
        self.cmd: str | None = None
        self.matrice_access_key_id: str | None = None
        self.matrice_secret_access_key: str | None = None
        self.action_info = action_info
        self.action_record_id = action_info["_id"]
        self.action_type = action_info["action"]
        self.action_details = action_info["actionDetails"]
        self.docker_container = self.action_details.get(
            "docker",
            self.action_details.get(
                "docker_container",
                self.scaling.get_data_processing_image(),
            ),
        )
        self.actions_map = {
            "model_train": model_train_execute,
            "model_eval": model_eval_execute,
            "model_export": model_export_execute,
            "deploy_add": model_deploy_execute,
            "data_import": data_processing_execute,
            "data_add": data_processing_execute,
            "data_split": data_split_execute,
            "data_prep": data_preparation_execute,
            "dataset_annotation": dataset_annotation_execute,
            "dataset_augmentation": dataset_augmentation_execute,
            "augmentation_setup": augmentation_server_creation_execute,
            "dataset_generation": synthetic_dataset_generation_execute,
            "synthetic_data_setup": synthetic_data_setup_execute,  # start
            "image_build": image_build_execute,
            "resource_clone": resource_clone_execute,
            "database_setup": database_setup_execute,
            "kafka_setup": kafka_setup_execute,
            "inference_aggregator": deploy_aggregator_execute,
            "redis_setup": redis_setup_execute,
            "streaming_gateway": streaming_gateway_execute,
            "facial_recognition_setup": facial_recognition_setup_execute,
            "fe_fs_streaming": fe_fs_streaming_execute,
            "inference_ws_server": inference_ws_server_execute,
            "fe_analytics_service": fe_analytics_service_execute,
            "lpr_setup": lpr_setup_execute,
            "inference_tracker_server": inference_tracker_setup_execute
        }
        if self.action_type not in self.actions_map:
            raise ValueError(f"Unknown action type: {self.action_type}")
        self.task = self.actions_map[self.action_type]

    @classmethod
    def is_first_deployment_for_service(cls, service_id):
        """Check if this is the first deployment for a given service.

        Args:
            service_id (str): Service ID (_idService)

        Returns:
            bool: True if this is the first deployment, False otherwise
        """
        if not service_id:
            return False
        return service_id not in cls._deployed_services

    @classmethod
    def get_or_create_triton_ports(cls, service_id, scaling_instance):
        """Get existing TRITON_PORTS for a service or create new ones.

        Args:
            service_id (str): Service ID (_idService)
            scaling_instance: Scaling instance to get open ports

        Returns:
            str: Comma-separated string of 3 port numbers (e.g., "8001,8002,8003")
        """
        if not service_id:
            # No service_id, generate new ports
            port1 = scaling_instance.get_open_port()
            port2 = scaling_instance.get_open_port()
            port3 = scaling_instance.get_open_port()
            return f"{port1},{port2},{port3}"

        # Check if ports already exist for this service
        if service_id in cls._deployed_services:
            triton_ports = cls._deployed_services[service_id]["triton_ports"]
            logging.info(
                "Reusing TRITON_PORTS for service %s: %s",
                service_id,
                triton_ports
            )
            return triton_ports

        # First deployment: generate new ports and store them
        port1 = scaling_instance.get_open_port()
        port2 = scaling_instance.get_open_port()
        port3 = scaling_instance.get_open_port()
        triton_ports = f"{port1},{port2},{port3}"

        # Store for future use
        cls._deployed_services[service_id] = {
            "triton_ports": triton_ports,
            "is_first": False
        }

        logging.info(
            "First deployment for service %s - generated TRITON_PORTS: %s",
            service_id,
            triton_ports
        )
        return triton_ports

    @log_errors(default_return={}, raise_exception=True, log_error=False)
    def _init_credentials(self):
        """Initialize Matrice credentials.

        Returns:
            dict: Dictionary containing access key ID and secret access key
        """
        self.matrice_access_key_id = self.scaling.session.access_key
        self.matrice_secret_access_key = self.scaling.session.secret_key
        if not all(
            [
                self.matrice_access_key_id,
                self.matrice_secret_access_key,
            ]
        ):
            raise ValueError(
                "Matrice credentials not found - both access key ID and secret access key are required"
            )
        return {
            "matrice_access_key_id": self.matrice_access_key_id,
            "matrice_secret_access_key": self.matrice_secret_access_key,
        }

    @log_errors(default_return="logs", raise_exception=False, log_error=False)
    def get_log_path(self):
        """Get log directory path, creating if needed.

        Returns:
            str: Path to log directory
        """
        os.makedirs("logs", exist_ok=True)
        return "logs"

    @log_errors(default_return=False, raise_exception=False, log_error=False)
    def is_running(self) -> bool:
        """Check if task process is running.

        This method performs a thorough check to determine if the process is still running:
        1. Verifies that the process attribute exists and is not None
        2. Checks if the process has terminated using poll() method
        3. Additional safeguards against zombie processes
        4. Coordinates with log monitoring to ensure all logs are sent before cleanup

        Returns:
            bool: True if process exists and is still running, False if process
                 does not exist or has terminated
        """
        # Basic check if process exists
        if not hasattr(self, "process") or self.process is None:
            return False

        try:
            # Check if process has terminated
            poll_result = self.process.poll()

            # poll() returns None if the process is still running
            is_running = poll_result is None

            # If process has terminated, ensure we do proper cleanup
            if not is_running:
                # Log termination with action ID for debugging
                action_id = getattr(self, "action_record_id", "unknown")
                logging.info(
                    "Process for action %s has terminated with exit code: %s",
                    action_id,
                    poll_result,
                )

                # CRITICAL: Ensure all logs are sent before cleaning up process
                self._ensure_final_logs_sent()

                # Try to explicitly clean up the process to avoid zombies
                try:
                    # Wait for process with a short timeout to ensure it's fully terminated
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    # If still running after timeout (unlikely at this point)
                    logging.warning(
                        f"Process for action {action_id} failed to terminate properly"
                    )

                # Set process to None to help garbage collection - BUT ONLY after logs are handled
                self.process = None

            return is_running

        except Exception as e:
            # Something went wrong while checking the process status
            logging.error(f"Error checking process status: {str(e)}")
            # Ensure logs are sent even in error cases
            self._ensure_final_logs_sent()
            # To be safe, assume process is not running when we can't check it
            self.process = None
            return False

    def _ensure_final_logs_sent(self):
        """Ensure all remaining logs are sent when a process terminates.

        This method performs a final log flush to ensure no logs are lost
        when a container crashes or shuts down.
        """
        if (
            not hasattr(self, "log_path")
            or not self.log_path
            or not os.path.exists(self.log_path)
        ):
            return

        try:
            # Set flag to stop continuous logging thread
            self.stop_thread = True

            # Give log thread a moment to finish current operation
            time.sleep(1)

            # Perform final log flush
            logging.info(
                "Performing final log flush for action %s",
                getattr(self, "action_record_id", "unknown"),
            )

            # Read any remaining logs that haven't been sent
            with open(self.log_path, "rb") as log_file:
                # Get the last position that was read (if tracked)
                last_position = getattr(self, "_last_log_position", 0)
                log_file.seek(last_position)
                remaining_content = log_file.read()

                if remaining_content:
                    try:
                        decoded_content = remaining_content.decode("utf-8")
                    except UnicodeDecodeError:
                        decoded_content = remaining_content.decode(
                            "utf-8", errors="replace"
                        )

                    # Send final logs
                    self._send_logs_to_scaling(decoded_content)
                    self._check_cuda(decoded_content)

                    logging.info(
                        "Sent %d bytes of final logs for action %s",
                        len(remaining_content),
                        getattr(self, "action_record_id", "unknown"),
                    )
                else:
                    logging.info(
                        "No additional logs to send for action %s",
                        getattr(self, "action_record_id", "unknown"),
                    )

        except Exception as e:
            logging.error(
                "Error during final log flush for action %s: %s",
                getattr(self, "action_record_id", "unknown"),
                str(e),
            )

    @log_errors(default_return=None, raise_exception=False, log_error=False)
    def get_action_details(self):
        """Get action details from scaling service.

        Returns:
            dict: Action details if successful, None otherwise
        """
        resp, error, message = self.scaling.get_action_details(self.action_record_id)
        if error:
            logging.error(
                "Error getting action details: %s",
                error,
            )
            return None
        return resp

    @log_errors(default_return="", raise_exception=False)
    def get_gpu_config(self, action_details):
        """Get GPU configuration string based on available GPUs.

        Args:
            action_details (dict): Action details containing GPU requirements

        Returns:
            str: GPU configuration string
        """
        action_id = action_details.get("_id", "unknown")

        # Check if GPU is required
        gpu_required = action_details["actionDetails"].get("gpuRequired", False)
        if not gpu_required:
            logging.info(
                "Action %s does not require GPU - will run on CPU",
                action_id
            )
            return ""

        # Get required GPU memory for logging
        required_memory = action_details.get("actionDetails", {}).get(
            "expectedResources", {}
        ).get("gpuMemory", 0)

        logging.info(
            "Action %s requires GPU with %d MB memory - selecting GPU(s) with most free memory",
            action_id,
            required_memory
        )

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
                # Format: --gpus "device=0" or --gpus "device=0,1,2"
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

    @log_errors(default_return="", raise_exception=False)
    def get_base_docker_cmd(
        self,
        work_fs: str = "",
        use_gpu: str = "",
        mount_docker_sock: bool = False,
        action_id: str = "",
        model_key: str = "",
        extra_env_vars: dict = {},
        port_mapping: dict = {},
        network_config: str = "",
        destination_workspace_path: str = "/usr/src/workspace",
        docker_workdir: str = "",
        extra_pkgs: list = [],
        container_name: str = "",
    ):
        """Build base Docker command with common options.

        Args:
            work_fs (str): Work filesystem path
            use_gpu (str): GPU configuration string
            mount_docker_sock (bool): Whether to mount Docker socket
            action_id (str): Action ID
            model_key (str): Model key
            extra_env_vars (dict): Additional environment variables
            port_mapping (dict): Port mappings {host_port: container_port}
            destination_workspace_path (str): Container workspace path
            docker_workdir (str): Docker working directory
            extra_pkgs (list): List of extra packages to install
            container_name (str): Docker container name (format: {action_type}_{action_id})
        Returns:
            str: Base Docker command
        """
        env = os.environ.get("ENV", "prod")
        env_vars = {
            "ENV": env,
            "MATRICE_SECRET_ACCESS_KEY": self.matrice_secret_access_key,
            "MATRICE_ACCESS_KEY_ID": self.matrice_access_key_id,
        }
        if self.get_hugging_face_token(model_key):
            env_vars["HUGGING_FACE_ACCESS_TOKEN"] = self.get_hugging_face_token(
                model_key
            )
        if extra_env_vars:
            env_vars.update(extra_env_vars)

        if network_config == "":
            network_config = (
                "--net=host"
                if not port_mapping
                else " ".join(
                    f"-p {host}:{container}" for host, container in port_mapping.items()
                )
            )

        if not docker_workdir:
            if action_id:
                docker_workdir = f"/usr/src/{action_id}"
            else:
                docker_workdir = "."
        volumes = [
            (  # Mount workspace if work_fs is provided
                f"-v {work_fs}/workspace:{destination_workspace_path}"
                if work_fs and work_fs not in ["/"]
                else ""
            ),
            (  # Mount action directory if work_fs and action_id are provided
                f"-v {work_fs}/{action_id}:/usr/src/{action_id}"
                if work_fs and work_fs not in ["/"] and action_id
                else ""
            ),
            "-v /var/run/docker.sock:/var/run/docker.sock" if mount_docker_sock else "",
        ]
        pypi_index = f"https://{'test.' if env != 'prod' else ''}pypi.org/simple/"
        
        pkgs = ["matrice_common", "matrice"]
        pkgs.extend(extra_pkgs)
        if env == 'dev':
            pkgs = [pkg + ">=1.0.0" for pkg in pkgs]
            pip_install_matrice = f"pip install --pre --upgrade --force-reinstall --index-url {pypi_index} {' '.join(pkgs)}"
        else:
            pip_install_matrice = f"pip install --upgrade --force-reinstall --index-url {pypi_index} {' '.join(pkgs)}"
        pip_install_requirements = (
            "if [ -f requirements.txt ]; then pip install -r requirements.txt; fi "
        )

        # Create export statements for environment variables to ensure they're available in subshells
        env_exports = " && ".join(
            [
                f"export {key}={shlex.quote(str(value))}"
                for key, value in env_vars.items()
            ]
        )

        # Build container name option if provided
        name_option = f"--name {container_name}" if container_name else ""

        cmd_parts = [
            f"docker run -d {use_gpu} ",
            name_option,
            network_config,
            *[f"-e {key}={shlex.quote(str(value))}" for key, value in env_vars.items()],
            *volumes,
            # Container configuration and startup commands
            f"--shm-size=30G --pull=always {shlex.quote(self.docker_container)}",
            f'/bin/bash -c "cd {docker_workdir} && '
            f"{env_exports} && "
            f"{pip_install_requirements} && "
            f"{pip_install_matrice} && ",
        ]

        # Join all non-empty parts with spaces
        return " ".join(filter(None, cmd_parts))

    @log_errors(default_return="", raise_exception=False)
    def get_hugging_face_token(self, model_key):
        """Get Hugging Face token for specific model keys.

        Args:
            model_key (str): Model key to check

        Returns:
            str: Hugging Face token if available, empty string otherwise
        """
        hugging_face_token = ""
        if model_key and (
            model_key.startswith("microsoft") or model_key.startswith("timm")
        ):
            secret_name = "hugging_face"
            resp, error, message = self.scaling.get_model_secret_keys(secret_name)
            if error is not None:
                logging.error(
                    "Error getting Hugging Face token: %s",
                    message,
                )
            else:
                hugging_face_token = resp["user_access_token"]
        return hugging_face_token

    @log_errors(default_return="", raise_exception=False)
    def get_hugging_face_token_for_data_generation(self):
        secret_name = "hugging_face"
        resp, error, message = self.scaling.get_model_secret_keys(secret_name)
        if error is not None:
            logging.error(
                "Error getting Hugging Face token: %s",
                message,
            )
        else:
            hugging_face_token = resp["user_access_token"]
        return hugging_face_token

    @log_errors(default_return="", raise_exception=False)
    def get_internal_api_key(self, action_id):
        """Get internal API key for action.

        Args:
            action_id (str): Action ID

        Returns:
            str: Internal API key if available, empty string otherwise
        """
        internal_api_key = ""
        resp, error, message = self.scaling.get_internal_api_key(action_id)
        if error is not None:
            logging.error(
                "Error getting internal api key: %s",
                message,
            )
        else:
            internal_api_key = resp["internal_api_key"]
        return internal_api_key

    @log_errors(raise_exception=True)
    def setup_action_requirements(
        self,
        action_details,
        work_fs="",
        model_family="",
        action_id="",
    ):
        """Setup action requirements.

        Args:
            action_details (dict): Action details
            work_fs (str): Work filesystem path
            model_family (str): Model family name
            action_id (str): Action ID

        Raises:
            Exception: If setup fails
        """
        # Get job parameters from action_details
        job_params = action_details.get("jobParams", {})

        # Setup model codebase if model_family is provided
        if model_family:
            # Try to get model codebase URLs from action_details first
            model_codebase_url = job_params.get("model_codebase_url")
            model_requirements_url = job_params.get("model_requirements_url")
            dockerId = job_params.get("_idDocker")

            # Fallback to API calls if not provided in action_details
            if not model_codebase_url:
                model_codebase_url, error, message = self.scaling.get_model_codebase(
                    dockerId
                )
                if error:
                    logging.warning(f"Failed to get model codebase URL: {message}")
                    model_codebase_url = None

            # Handle requirements URL - use from job_params or get from API
            if model_requirements_url:
                model_codebase_requirements_url = model_requirements_url
            else:
                model_codebase_requirements_url, error, message = (
                    self.scaling.get_model_codebase_requirements(dockerId)
                )
                if error:
                    logging.warning(
                        f"Failed to get model codebase requirements URL: {message}"
                    )
                    model_codebase_requirements_url = None

            # Setup workspace if we have the URLs
            if model_codebase_url:
                setup_workspace_and_run_task(
                    work_fs,
                    action_id,
                    model_codebase_url,
                    model_codebase_requirements_url,
                )

        # Setup Docker credentials
        try:
            # Try to get Docker credentials from action_details first
            docker_username = job_params.get("Username")
            docker_password = job_params.get("Password")
            if docker_username and docker_password:
                username = docker_username
                password = docker_password
                logging.info("Using Docker credentials from action_details")
            else:
                # Fallback to API call
                creds, error, message = self.scaling.get_docker_hub_credentials()
                if error:
                    raise Exception(f"Failed to get Docker credentials: {message}")
                username = creds["username"]
                password = creds["password"]
                logging.info("Using Docker credentials from API call")

            if username and password:
                login_cmd = f"docker login -u {shlex.quote(username)} -p {shlex.quote(password)}"
                result = subprocess.run(login_cmd, shell=True, check=False, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise Exception(f"Docker login failed with exit code {result.returncode}: {result.stderr}")
                logging.info("Docker login successful")
            else:
                logging.warning(
                    "Docker credentials not available, skipping Docker login"
                )

        except subprocess.TimeoutExpired:
            logging.error("Docker login timed out after 30 seconds")
            raise Exception("Docker login timed out")
        except Exception as err:
            logging.error(
                "Docker login failed: %s",
                str(err),
            )
            raise

        # Setup user access credentials
        try:
            # Try to get access key and secret key from job_params first
            access_key = job_params.get("access_key")
            secret_key = job_params.get("secret_key")

            if access_key and secret_key:
                logging.info("Using access key and secret key from job_params")
                (
                    self.matrice_access_key_id,
                    self.matrice_secret_access_key,
                ) = get_decrypted_access_key_pair(access_key, secret_key)
            else:
                # Fallback to API call
                logging.info(
                    "Access key and secret key not found in job_params, falling back to API call"
                )
                (
                    user_access_key_pair,
                    error,
                    message,
                ) = self.scaling.get_user_access_key_pair(action_details["_idUser"])
                if error:
                    raise Exception(f"Failed to get user access key pair: {message}")
                access_key = user_access_key_pair["access_key"]
                secret_key = user_access_key_pair["secret_key"]
                (
                    self.matrice_access_key_id,
                    self.matrice_secret_access_key,
                ) = get_decrypted_access_key_pair(access_key, secret_key)

        except Exception as err:
            logging.error(
                "Failed to setup credentials: %s",
                str(err),
            )
            raise

    # @log_errors(raise_exception=False)
    # def create_redis_container(self, redis_image=None, redis_password=None):
    #     """Create and start a Redis container using Docker.

    #     Args:
    #         redis_image (str, optional): Redis Docker image to use. Defaults to 'redis:latest'

    #     Returns:
    #         tuple: (container_info, error, message)
    #     """
    #     if redis_image is None:
    #         redis_image = "redis:latest"

    #     network_name = f"redis_network_{int(time.time())}"
    #     subprocess.run(f"docker network create {network_name}", shell=True, check=True)

    #     try:
    #         # Get an available port for Redis
    #         external_port = "6379"

    #         # Generate a unique container name and password
    #         container_name = f"redis_container_{int(time.time())}"

    #         # Build the docker command to create Redis container with password
    #         cmd = (
    #             f"docker run -d "
    #             f"--network {network_name} "
    #             f"--name {container_name} "
    #             f"-p {external_port}:6379 "
    #             f"--restart unless-stopped "
    #             f"{redis_image} "
    #             f"redis-server --bind 0.0.0.0 --appendonly yes --requirepass {redis_password}"
    #         )

    #         logging.info("Creating Redis container with command: %s", cmd)

    #         # Execute the command
    #         result = subprocess.run(
    #             cmd, shell=True, capture_output=True, text=True, timeout=60
    #         )

    #         if result.returncode == 0:
    #             container_id = result.stdout.strip()
    #             container_info = {
    #                 "container_id": container_id,
    #                 "container_name": container_name,
    #                 "network_name": network_name,
    #                 "external_port": external_port,
    #                 "internal_port": 6379,
    #                 "password": redis_password,
    #                 "image": redis_image,
    #                 "status": "running",
    #             }

    #             logging.info("Redis container created successfully: %s", container_info)
    #             return container_info, None, "Redis container created successfully"
    #         else:
    #             error_message = f"Failed to create Redis container: {result.stderr}"
    #             logging.error(error_message)
    #             return None, "ContainerCreationError", error_message

    #     except subprocess.TimeoutExpired:
    #         error_message = "Timeout while creating Redis container"
    #         logging.error(error_message)
    #         return None, "TimeoutError", error_message
    #     except Exception as e:
    #         error_message = f"Unexpected error creating Redis container: {str(e)}"
    #         logging.error(error_message)
    #         return None, "UnexpectedError", error_message

    @log_errors(raise_exception=False, log_error=False)
    def send_logs_continuously(self):
        """Continuously read and send logs from the log file to the scaling service.

        Enhanced version that tracks log position and handles graceful shutdown.
        """
        last_position = 0
        self._last_log_position = 0  # Track position for final flush

        while not self.stop_thread and os.path.exists(self.log_path):
            try:
                with open(self.log_path, "rb") as log_file:
                    log_file.seek(last_position)
                    new_content = log_file.read()
                    if new_content:
                        try:
                            decoded_content = new_content.decode("utf-8")
                        except UnicodeDecodeError:
                            # Handle invalid UTF-8 bytes by replacing them
                            decoded_content = new_content.decode(
                                "utf-8",
                                errors="replace",
                            )
                        self._send_logs_to_scaling(decoded_content)
                        self._check_cuda(decoded_content)

                    # Update tracked position
                    last_position = log_file.tell()
                    self._last_log_position = last_position

            except Exception as e:
                logging.error(
                    "Error reading logs for action %s: %s",
                    getattr(self, "action_record_id", "unknown"),
                    str(e),
                )

            # Use shorter sleep interval for more responsive log monitoring
            time.sleep(10)  # Reduced from 30 to 10 seconds for better responsiveness

        # Final attempt to send any remaining logs when thread is stopping
        logging.info(
            "Log monitoring thread stopping for action %s, performing final check",
            getattr(self, "action_record_id", "unknown"),
        )

        # One more final read attempt
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, "rb") as log_file:
                    log_file.seek(last_position)
                    final_content = log_file.read()
                    if final_content:
                        try:
                            decoded_content = final_content.decode("utf-8")
                        except UnicodeDecodeError:
                            decoded_content = final_content.decode(
                                "utf-8", errors="replace"
                            )
                        self._send_logs_to_scaling(decoded_content)
                        self._check_cuda(decoded_content)
                        logging.info(
                            "Sent final %d bytes of logs for action %s",
                            len(final_content),
                            getattr(self, "action_record_id", "unknown"),
                        )
        except Exception as e:
            logging.error(
                "Error in final log read for action %s: %s",
                getattr(self, "action_record_id", "unknown"),
                str(e),
            )

    @log_errors(raise_exception=False, log_error=False)
    def _send_logs_to_scaling(self, log_content):
        """Send logs to the scaling service.

        Args:
            log_content (str): Log content to send
        """
        _, error, message = self.scaling.update_action_docker_logs(
            action_record_id=self.action_record_id,
            log_content=log_content,
        )
        if error:
            logging.error(
                "Error from update_action_docker_logs: %s",
                error,
            )

    @log_errors(raise_exception=False, log_error=False)
    def _check_cuda(self, log_content):
        """Check for CUDA out of memory errors in logs and update action status.

        Args:
            log_content (str): Log content to check
        """
        if "CUDA error: out of memory" in log_content:
            action_details = self.get_action_details()
            if not action_details:
                return
            self.scaling.update_action(
                id=self.action_record_id,
                step_code="ERROR",
                action_type=action_details["action"],
                status="ERROR",
                status_description="CUDA error: out of memory",
                service="bg-job-scheduler",
                job_params=action_details["jobParams"],
            )

    @staticmethod
    def container_exists(container_id: str) -> bool:
        """Check if a Docker container exists.

        Args:
            container_id (str): Container ID or name to check

        Returns:
            bool: True if container exists, False otherwise
        """
        if not container_id:
            return False
        try:
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logging.warning(
                "Error checking if container %s exists: %s",
                container_id,
                str(e)
            )
            return False

    @log_errors(raise_exception=True)
    def start_process(self, cmd, log_name):
        """Start the process and initialize logging.

        Args:
            cmd (str): Command to execute
            log_name (str): Name for log file

        Raises:
            Exception: If process fails to start
        """
        self.cmd = cmd
        self.log_path = f"{self.get_log_path()}/{log_name}_{self.action_record_id}.txt"

        # Run docker with -d flag to get container ID from stdout
        process = subprocess.Popen(
            shlex.split(self.cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ},
        )
        
        # Use a longer timeout for docker run since --pull=always may need to
        # download large images on first run. Default: 30 minutes (1800 seconds)
        # Can be configured via DOCKER_START_TIMEOUT_SECONDS environment variable
        docker_start_timeout = int(os.environ.get("DOCKER_START_TIMEOUT_SECONDS", 1800))
        logging.info(
            "Waiting for docker container to start for action %s (timeout: %d seconds)",
            self.action_record_id,
            docker_start_timeout,
        )
        stdout, stderr = process.communicate(timeout=docker_start_timeout)
        
        if process.returncode != 0:
            logging.error(
                "Docker run failed for action %s: %s",
                self.action_record_id,
                stderr,
            )
            raise RuntimeError(f"Docker run failed: {stderr}")
        
        self.container_id = stdout.strip()
        logging.info(
            "Started container for action %s with ID: %s",
            self.action_record_id,
            self.container_id,
        )
        
        # Start following container logs in background
        self.process = subprocess.Popen(
            ["docker", "logs", "-f", self.container_id],
            stdout=open(self.log_path, "wb"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        
        # Report container id to scaling service
        self.scaling.update_action_container_id(
            action_record_id=self.action_record_id,
            container_id=self.container_id,
        )

    @log_errors(raise_exception=False)
    def start_logger(self):
        """Start the log monitoring thread."""
        self.log_thread = threading.Thread(
            target=self.send_logs_continuously,
            daemon=False,  # CRITICAL: Make thread non-daemon to ensure it completes
        )
        self.log_thread.start()

    @log_errors(raise_exception=False)
    def start(self, cmd: str = "", log_name: str = ""):
        """Start the process and log monitoring thread.

        Args:
            cmd (str): Command to execute
            log_name (str): Name for log file
        """
        self.start_process(cmd, log_name)
        self.start_logger()
        self.scaling.update_status(
            self.action_record_id,
            self.action_type,
            "bg-job-scheduler",
            "DKR_CMD",
            "OK",
            f"Start docker container with command: {cmd.replace(self.matrice_access_key_id, 'MATRICE_ACCESS_KEY_ID').replace(self.matrice_secret_access_key, 'MATRICE_SECRET_ACCESS_KEY')}",
        )

    @log_errors(raise_exception=False, log_error=False)
    def stop(self):
        """Stop the process and log monitoring thread.

        Enhanced version that ensures proper cleanup sequencing and log completion.
        """
        logging.info("Stopping action %s", getattr(self, "action_record_id", "unknown"))

        # Step 1: Signal log thread to stop
        self.stop_thread = True

        # Step 2: Stop the process
        try:
            if self.process:
                logging.info(
                    "Terminating process for action %s",
                    getattr(self, "action_record_id", "unknown"),
                )
                os.killpg(
                    os.getpgid(self.process.pid),
                    signal.SIGTERM,
                )
                # Give process time to terminate gracefully
                try:
                    self.process.wait(timeout=15)
                    logging.info(
                        "Process terminated gracefully for action %s",
                        getattr(self, "action_record_id", "unknown"),
                    )
                except subprocess.TimeoutExpired:
                    logging.warning(
                        "Process didn't terminate gracefully, forcing kill for action %s",
                        getattr(self, "action_record_id", "unknown"),
                    )
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                        self.process.wait(timeout=5)
                    except Exception as kill_err:
                        logging.error(
                            "Error force-killing process for action %s: %s",
                            getattr(self, "action_record_id", "unknown"),
                            str(kill_err),
                        )
        except Exception as proc_err:
            logging.error(
                "Error stopping process for action %s: %s",
                getattr(self, "action_record_id", "unknown"),
                str(proc_err),
            )

        # Step 3: Ensure final logs are sent
        self._ensure_final_logs_sent()

        # Step 4: Wait for log thread to complete
        if self.log_thread and self.log_thread.is_alive():
            logging.info(
                "Waiting for log thread to complete for action %s",
                getattr(self, "action_record_id", "unknown"),
            )
            try:
                self.log_thread.join(
                    timeout=30
                )  # Wait up to 30 seconds for logs to complete
                if self.log_thread.is_alive():
                    logging.warning(
                        "Log thread didn't complete within timeout for action %s",
                        getattr(self, "action_record_id", "unknown"),
                    )
                else:
                    logging.info(
                        "Log thread completed successfully for action %s",
                        getattr(self, "action_record_id", "unknown"),
                    )
            except Exception as thread_err:
                logging.error(
                    "Error waiting for log thread for action %s: %s",
                    getattr(self, "action_record_id", "unknown"),
                    str(thread_err),
                )

    @log_errors(raise_exception=False)
    def execute(self):
        """Execute the task."""
        self.task(self)


@log_errors(raise_exception=False)
def data_preparation_execute(
    self: ActionInstance,
):
    """Execute data preparation task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs, model_family="")
    action = {"jobParams": action_details["jobParams"]}
    dataset_id_version = (
        action_details["jobParams"]["dataset_id"]
        + action_details["jobParams"]["dataset_version"]
    )
    action["jobParams"].update(
        {
            "dataset_host_path_map": {dataset_id_version: f"{work_fs}/workspace"},
            "dataset_local_path_map": {dataset_id_version: "/usr/src/app/workspace"},
            "host_file_system": work_fs,
        }
    )
    self.scaling.update_action(
        id=self.action_record_id,
        step_code="DCK_LNCH",
        action_type=action_details["action"],
        status=action_details["status"],
        sub_action=action_details["subAction"],
        status_description="Job is assigned to docker",
        service="bg-job-scheduler",
        job_params=action["jobParams"],
    )
    if action["jobParams"].get("model_train_docker"):
        logging.info("Pulling the docker image")
        pull_cmd = f"docker pull {action['jobParams']['model_train_docker']}"
        process = subprocess.Popen(
            pull_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.info(
            "Started pulling Docker image with PID: %s",
            process.pid,
        )
    container_name = f"data_prep_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, destination_workspace_path="/usr/src/app/workspace", docker_workdir="/usr/src/app/workspace", extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/data_preparation.py {self.action_record_id} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "data_preparation_log")


@log_errors(raise_exception=False)
def data_processing_execute(self: ActionInstance):
    """Execute data processing task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs, model_family="")
    action = {"jobParams": action_details["jobParams"]}
    action["jobParams"].update(
        {
            "dp_dv_host_paths": [f"{work_fs}/workspace"],
            "dp_dv_local_paths": ["/usr/src/app/workspace"],
        }
    )
    self.scaling.update_action(
        id=self.action_record_id,
        step_code="DCK_LNCH",
        action_type=action_details["action"],
        status="ACK",
        status_description="Job is assigned to docker",
        service="bg-job-scheduler",
        job_params=action["jobParams"],
    )
    container_name = f"data_processing_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/main.py {self.action_record_id} "'
    logging.info("cmd: %s", cmd)
    self.start(cmd, "data_processing_log")


@log_errors(raise_exception=False)
def data_split_execute(self: ActionInstance):
    """Execute data split task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs, model_family="")
    container_name = f"data_split_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/data_split.py {self.action_record_id} "'
    logging.info("cmd: %s", cmd)
    self.start(cmd, "data_split")


@log_errors(raise_exception=False)
def dataset_annotation_execute(
    self: ActionInstance,
):
    """Execute dataset annotation task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs)
    container_name = f"dataset_annotation_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/dataset_annotation.py {self.action_record_id} "'
    logging.info("cmd: %s", cmd)
    self.start(cmd, "dataset_annotation")


@log_errors(raise_exception=False)
def dataset_augmentation_execute(
    self: ActionInstance,
):
    """Execute dataset augmentation task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs)
    container_name = f"dataset_augmentation_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/data_augmentation.py {self.action_record_id} "'
    logging.info("cmd: %s", cmd)
    self.start(cmd, "dataset_augmentation")


@log_errors(raise_exception=False)
def augmentation_server_creation_execute(
    self: ActionInstance,
):
    """Create Augmentation Server"""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    external_port = self.scaling.get_open_port()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs)
    container_name = f"augmentation_setup_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/aug_server.py {self.action_record_id} {external_port} "'
    logging.info("cmd: %s", cmd)
    self.start(cmd, "augmentation_setup")


@log_errors(raise_exception=False)
def database_setup_execute(self: ActionInstance):
    """
    Creates and setup the database for facial recognition server.
    MongoDB runs on port 27020:27017 (localhost only with --net=host).
    Qdrant runs on port 6334 (localhost only with --net=host).
    """
    action_details = self.get_action_details()
    if not action_details:
        return
    image = action_details["actionDetails"].get("docker")

    self.setup_action_requirements(action_details)

    project_id = action_details["_idProject"]

    # Define container names with action_record_id for uniqueness
    mongodb_container_name = f"database_setup_{self.action_record_id}"
    qdrant_container_name = f"qdrant_{self.action_record_id}"

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if both containers actually exist before trying to restart
        mongodb_container_exists = ActionInstance.container_exists(existing_container_id)
        qdrant_container_exists = ActionInstance.container_exists(qdrant_container_name)

        if mongodb_container_exists and qdrant_container_exists:
            logging.info(
                "Using existing container ID for database setup: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "qdrant_setup")

            # qdrant restart
            qdrant_cmd = f"docker restart {qdrant_container_name}"
            self.start(qdrant_cmd, "qdrant_setup")
            return
        else:
            logging.warning(
                "Container(s) not found (mongodb=%s, qdrant=%s). Creating new containers.",
                mongodb_container_exists,
                qdrant_container_exists
            )
            # Fall through to create new containers

    # MongoDB container with --net=host (Port: 27020:27017)
    cmd = (
        f"docker run --pull=always --net=host "
        f"--name {mongodb_container_name} "
        f"-v matrice_myvol:/matrice_data "
        f"--cidfile ./{self.action_record_id}.cid "
        f"-e ACTION_RECORD_ID={self.action_record_id} "
        f"-e MATRICE_ACCESS_KEY_ID={self.matrice_access_key_id} "
        f"-e MATRICE_SECRET_ACCESS_KEY={self.matrice_secret_access_key} "
        f"-e PROJECT_ID={project_id} "
        f'-e ENV="{os.environ.get("ENV", "prod")}" '
        f"{image} "
    )
    logging.info("Starting MongoDB container (Port: 27020:27017): %s", cmd)

    # Qdrant container with --net=host (Port: 6334)
    qdrant_cmd = (
        f"docker run --pull=always --net=host "
        f"--name {qdrant_container_name} "
        f"-v matrice_myvol:/matrice_data "
        f"{'qdrant/qdrant:latest'} "
    )
    logging.info("Starting Qdrant container (Port: 6334): %s", qdrant_cmd)

    # Docker Command run
    self.start(cmd, "database_setup") 

    # Docker for qdrant
    self.start(qdrant_cmd, 'qdrant_setup')

@log_errors(raise_exception=False)
def facial_recognition_setup_execute(self: ActionInstance):
    """
    Creates and setup the facial recognition worker server.
    Facial recognition worker runs on port 8081 (localhost only with --net=host).
    """
    action_details = self.get_action_details()

    if not action_details:
        return
    image = action_details["actionDetails"].get("docker")

    self.setup_action_requirements(action_details)

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for facial recognition worker: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "facial_recognition_setup")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    # Facial recognition worker container with --net=host (Port: 8081)
    container_name = f"facial_recognition_{self.action_record_id}"
    worker_cmd = (
        f"docker run -d --pull=always --net=host "
        f"--name {container_name} "
        f"--cidfile ./{self.action_record_id}.cid "
        f"-v matrice_myvol:/matrice_data "
        f'-e ENV="{os.environ.get("ENV", "prod")}" '
        f'-e MATRICE_SECRET_ACCESS_KEY="{self.matrice_secret_access_key}" '
        f'-e MATRICE_ACCESS_KEY_ID="{self.matrice_access_key_id}" '
        f'-e ACTION_ID="{self.action_record_id}" '
        f"{image}"
    )
    logging.info("Starting facial recognition worker (Port: 8081): %s", worker_cmd)

    # Docker Command run
    self.start(worker_cmd, "facial_recognition_setup")

@log_errors(raise_exception=False)
def lpr_setup_execute(self: ActionInstance):
    """
    Creates and setup the license plate recognition server.
    LPR worker runs on port 8082 (localhost only with --net=host).
    """
    action_details = self.get_action_details()

    if not action_details:
        return
    image = self.docker_container

    self.setup_action_requirements(action_details)

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for LPR worker: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "lpr_setup")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    # LPR worker container with --net=host (Port: 8082)
    container_name = f"lpr_{self.action_record_id}"
    worker_cmd = (
        f"docker run -d --net=host --pull=always "
        f"--name {container_name} "
        f"--cidfile ./{self.action_record_id}.cid "
        f"-v matrice_myvol:/matrice_data "
        f'-e ENV="{os.environ.get("ENV", "prod")}" '
        f'-e MATRICE_SECRET_ACCESS_KEY="{self.matrice_secret_access_key}" '
        f'-e MATRICE_ACCESS_KEY_ID="{self.matrice_access_key_id}" '
        f'-e ACTION_ID="{self.action_record_id}" '
        f'-e PORT=8082 '
        f"{image}"
    )
    logging.info("Starting LPR worker (Port: 8082): %s", worker_cmd)

    # Docker Command run
    self.start(worker_cmd, "lpr_setup")

@log_errors(raise_exception=False)
def inference_ws_server_execute(self: ActionInstance):
    """
    Creates and start inference pipeline.
    Inference WebSocket server runs on port 8102 (localhost only with --net=host).
    """
    action_details = self.get_action_details()

    if not action_details:
        return
    image = action_details["actionDetails"].get("docker")
    
    self.setup_action_requirements(action_details)

    # Get the best IP and network configuration for port 8102
    ws_host, use_host_network = get_best_service_ip_and_network(8102)
    
    # Store ws_host in environment variable for use by other actions (e.g., fe_fs_streaming)
    if not os.environ.get("INFERENCE_WS_HOST"):
        os.environ["INFERENCE_WS_HOST"] = ws_host
    
    logging.info(f"Inference WebSocket server will use IP: {ws_host} on port 8102 (use_host_network={use_host_network})")

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for inference WebSocket server: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "inference_ws_server")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    # Inference WebSocket server with --net=host (Port: 8102)
    container_name = f"inference_ws_{self.action_record_id}"
    worker_cmd = (
        f"docker run -d --pull=always --net=host "
        f"--name {container_name} "
        f"--cidfile ./{self.action_record_id}.cid "
        f'-e ENV="{os.environ.get("ENV", "prod")}" '
        f'-e MATRICE_SECRET_ACCESS_KEY="{self.matrice_secret_access_key}" '
        f'-e MATRICE_ACCESS_KEY_ID="{self.matrice_access_key_id}" '
        f"{image} "
        f"./app "
        f"{self.action_record_id} "
    )
    logging.info("Starting inference WebSocket server (Port: 8102): %s", worker_cmd)

    # Docker Command run
    self.start(worker_cmd, "inference_ws_server")


@log_errors(raise_exception=False)
def fe_fs_streaming_execute(self: ActionInstance):
    """
    Creates and setup the frontend for fs streaming.
    Frontend streaming runs on port 3000 (localhost only with --net=host).
    """
    action_details = self.get_action_details()

    if not action_details:
        return
    image = action_details["actionDetails"].get("docker")

    self.setup_action_requirements(action_details)
    
    # Get the ws_host from environment variable set by inference_ws_server_execute
    ws_host = os.environ.get("INFERENCE_WS_HOST", "localhost")
    ws_url = f"{ws_host}:8102"
    
    logging.info(f"Frontend streaming will connect to WebSocket at: {ws_url}")

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for frontend streaming: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "fe_fs_streaming")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    # Frontend streaming with --net=host (Port: 3000)
    container_name = f"fe_streaming_{self.action_record_id}"
    worker_cmd = (
        f"docker run -d --pull=always --net=host "
        f"--name {container_name} "
        f"--cidfile ./{self.action_record_id}.cid "
        f"-v matrice_myvol:/matrice_data "
        f'-e ENV="{os.environ.get("ENV", "prod")}" '
        f'-e MATRICE_SECRET_ACCESS_KEY="{self.matrice_secret_access_key}" '
        f'-e MATRICE_ACCESS_KEY_ID="{self.matrice_access_key_id}" '
        f"-e PORT=3000 "
        f'-e WS_HOST="{ws_url}" '
        f"{image}"
    )
    logging.info("Starting frontend streaming (Port: 3000) with WS_HOST=%s: %s", ws_url, worker_cmd)

    # Docker Command run
    self.start(worker_cmd, "fe_fs_streaming")


@log_errors(raise_exception=False)
def fe_analytics_service_execute(self: ActionInstance):
    """
    Creates and setup the frontend analytics service.
    Frontend analytics service runs on port 3001 (localhost only with --net=host).
    """
    action_details = self.get_action_details()

    if not action_details:
        return
    image = action_details["actionDetails"].get("docker")

    self.setup_action_requirements(action_details)

    project_id = action_details["_idProject"]

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for frontend analytics service: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "fe_analytics_service")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    # Frontend analytics service with --net=host (Port: 3001)
    container_name = f"fe_analytics_{self.action_record_id}"
    worker_cmd = (
        f"docker run -d --pull=always --net=host "
        f"--name {container_name} "
        f"--cidfile ./{self.action_record_id}.cid "
        f'-e NEXT_PUBLIC_DEPLOYMENT_ENV="{os.environ.get("ENV", "prod")}" '
        f'-e MATRICE_SECRET_ACCESS_KEY="{self.matrice_secret_access_key}" '
        f'-e MATRICE_ACCESS_KEY_ID="{self.matrice_access_key_id}" '
        f'-e ACTION_ID="{self.action_record_id}" '
        f"-e PORT=3001 "
        f'-e PROJECT_ID="{project_id}" '
        f"{image}"
    )
    logging.info("Starting frontend analytics service (Port: 3001): %s", worker_cmd)

    # Docker Command run
    self.start(worker_cmd, "fe_analytics_service")


@log_errors(raise_exception=False)
def synthetic_dataset_generation_execute(self: ActionInstance):
    """Execute synthetic dataset generation task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs)
    extra_env_vars = {}
    hf_token = self.get_hugging_face_token_for_data_generation()
    extra_env_vars["HUGGING_FACE_ACCESS_TOKEN"] = hf_token
    if hf_token:
        extra_env_vars["HUGGING_FACE_ACCESS_TOKEN"] = hf_token
    else:
        return
    use_gpu = self.get_gpu_config(action_details)
    container_name = f"dataset_generation_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs=work_fs, use_gpu=use_gpu, extra_env_vars=extra_env_vars, extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/synthetic_dataset_generation.py {self.action_record_id} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "dataset_generation")


@log_errors(raise_exception=False)
def synthetic_data_setup_execute(self: ActionInstance):
    """Execute synthetic data setup task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    external_port = self.scaling.get_open_port()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs)
    extra_env_vars = {}
    hf_token = self.get_hugging_face_token_for_data_generation()
    if hf_token:
        extra_env_vars["HUGGING_FACE_ACCESS_TOKEN"] = hf_token
    else:
        return
    use_gpu = self.get_gpu_config(action_details)
    container_name = f"synthetic_data_setup_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs=work_fs, use_gpu=use_gpu, extra_env_vars=extra_env_vars, extra_pkgs=["matrice_dataset"], container_name=container_name)} python3 /usr/src/app/data_generation.py {self.action_record_id} {external_port} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "synthetic_data_setup")


@log_errors(raise_exception=False)
def redis_setup_execute(self: ActionInstance):
    """
    Creates and starts a Redis container using Docker.
    Redis runs on port 6379 (localhost only with --net=host).
    """
    work_fs = get_max_file_system()

    action_details = self.get_action_details()
    if not action_details:
        return
    action_id = action_details["_id"]

    redis_password = action_details["jobParams"].get(
        "password", f"redis_pass_{int(time.time())}"
    )

    # Initialize redis container
    self.setup_action_requirements(
        action_details,
        work_fs,
        model_family="",
        action_id=action_id,
    )

    # Get the best IP for Redis (port 6379)
    redis_host, _ = get_best_service_ip_and_network(6379)
    
    logging.info(f"Redis will use IP: {redis_host} on port 6379")

    redis_image = action_details["actionDetails"].get("redis_image", "redis:latest")

    # Define container names with action_record_id for uniqueness
    redis_container_name = f"redis_{self.action_record_id}"

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if both containers actually exist before trying to restart
        management_container_exists = ActionInstance.container_exists(existing_container_id)
        redis_container_exists = ActionInstance.container_exists(redis_container_name)

        if management_container_exists and redis_container_exists:
            logging.info(
                "Using existing container ID for redis management: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "redis_setup")

            # Redis container restart
            redis_restart_cmd = f"docker restart {redis_container_name}"
            self.start(redis_restart_cmd, "redis")
            return
        else:
            logging.warning(
                "Container(s) not found (management=%s, redis=%s). Creating new containers.",
                management_container_exists,
                redis_container_exists
            )
            # Fall through to create new containers

    # Redis container with --net=host (Port: 6379)
    redis_cmd = (
        f"docker run -d --net=host "
        f"--name {redis_container_name} "
        f"--restart unless-stopped "
        f"{redis_image} "
        f"redis-server --bind 0.0.0.0 "
        f"--appendonly no "
        f'--save "" '
        f"--maxmemory 30gb "
        f"--maxmemory-policy allkeys-lru "
        f"--io-threads 4 "
        f"--io-threads-do-reads yes "
        f"--stream-node-max-bytes 8192 "
        f"--stream-node-max-entries 1000 "
        f"--hz 100 "
        f"--tcp-backlog 2048 "
        f"--timeout 0 "
        f"--lazyfree-lazy-eviction yes "
        f"--lazyfree-lazy-expire yes "
        f"--lazyfree-lazy-server-del yes "
        f"--activedefrag yes "
        f"--requirepass {redis_password}"
    )
    logging.info("Starting Redis container on %s:6379: %s", redis_host, redis_cmd)
    
    # Start Redis container first
    redis_process = subprocess.Popen(
        redis_cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    logging.info("Redis container started successfully on %s:6379", redis_host)
    
    # Wait for Redis to be ready
    time.sleep(5)

    env_vars = {
        "REDIS_URL": f"{redis_host}:6379",
        "REDIS_PASSWORD": redis_password,
    }

    # bg-redis management container with --net=host (Port: 8082)
    cmd = (
        f"docker run --net=host "
         f"--cidfile ./{self.action_record_id}.cid "
        f"-e REDIS_URL={shlex.quote(env_vars['REDIS_URL'])} "
        f"-e REDIS_PASSWORD={shlex.quote(env_vars['REDIS_PASSWORD'])} "
        f"-e MATRICE_ACCESS_KEY_ID={shlex.quote(self.matrice_access_key_id)} "
        f"-e MATRICE_SECRET_ACCESS_KEY={shlex.quote(self.matrice_secret_access_key)} "
        f"-e ENV={shlex.quote(os.environ.get('ENV', 'prod'))} "
        f"-v /var/run/docker.sock:/var/run/docker.sock "
        f"--shm-size=30G --pull=always "
        f"{self.docker_container} "
        f"{self.action_record_id} "
    )

    logging.info("Starting bg-redis management (Port: 8082) with REDIS_URL=%s: %s", env_vars['REDIS_URL'], cmd)

    self.start(cmd, "redis_setup")


@log_errors(raise_exception=False)
def deploy_aggregator_execute(
    self: ActionInstance,
):
    """Execute deploy aggregator task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details, work_fs)
    container_name = f"deploy_aggregator_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, container_name=container_name)} python3 /usr/src/app/deploy_aggregator.py {self.action_record_id} "'
    logging.info("cmd: %s", cmd)
    self.start(cmd, "deploy_aggregator")


@log_errors(raise_exception=False)
def model_deploy_execute(self: ActionInstance):
    """Execute model deployment task."""
    external_port = self.scaling.get_open_port()
    internal_port = self.scaling.get_open_port()
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    action_id = action_details["_id"]
    model_family = action_details["actionDetails"]["modelFamily"]

    # Get the service ID to track deployments
    service_id = action_details.get("_idService")

    self.setup_action_requirements(
        action_details,
        work_fs,
        model_family=model_family,
        action_id=action_id,
    )

    # Check if this is the first deployment for this service
    is_first_deployment = ActionInstance.is_first_deployment_for_service(service_id)

    # Get GPU configuration (uses utility function with fail-safe fallback)
    use_gpu = get_gpu_config_for_deployment(action_details, is_first_deployment)

    logging.info(
        "Action %s: Model deployment GPU config: %s (first_deployment=%s)",
        action_id,
        use_gpu if use_gpu else "CPU-only",
        is_first_deployment
    )

    # Get or create TRITON_PORTS (uses utility method)
    triton_ports = ActionInstance.get_or_create_triton_ports(service_id, self.scaling)

    extra_env_vars = {
        "INTERNAL_PORT": internal_port,
        "TRITON_PORTS": triton_ports
    }

    container_name = f"model_deploy_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, use_gpu, mount_docker_sock=True, action_id=action_id, extra_env_vars=extra_env_vars, extra_pkgs=["matrice_inference", "matrice_analytics"], container_name=container_name)} python3 deploy.py {self.action_record_id} {external_port}"'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "deploy_log")


@log_errors(raise_exception=False)
def model_train_execute(self: ActionInstance):
    """Execute model training task."""
    action_details = self.get_action_details()
    if not action_details:
        return
    action_id = action_details["_id"]
    use_gpu = self.get_gpu_config(action_details)
    work_fs = action_details["jobParams"]["host_file_system"]
    model_key = action_details["actionDetails"]["modelKey"]
    model_family = action_details["actionDetails"]["modelFamily"]
    self.setup_action_requirements(
        action_details,
        work_fs,
        model_family=model_family,
        action_id=action_id,
    )

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for training: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "train_log")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    container_name = f"model_train_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, use_gpu, action_id=action_id, model_key=model_key, container_name=container_name)} python3 train.py {self.action_record_id} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "train_log")


@log_errors(raise_exception=False)
def model_eval_execute(self: ActionInstance):
    """Execute model evaluation task."""
    action_details = self.get_action_details()
    if not action_details:
        return
    action_id = action_details["_id"]
    work_fs = action_details["jobParams"]["host_file_system"]
    model_family = action_details["actionDetails"]["modelFamily"]
    use_gpu = self.get_gpu_config(action_details)
    self.setup_action_requirements(
        action_details,
        work_fs,
        model_family=model_family,
        action_id=action_id,
    )
    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for evaluation: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "eval_log")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    container_name = f"model_eval_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, use_gpu, action_id=action_id, container_name=container_name)} python3 eval.py {self.action_record_id} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "eval_log")


@log_errors(raise_exception=False)
def model_export_execute(self: ActionInstance):
    """Execute model export task."""
    work_fs = get_max_file_system()
    action_details = self.get_action_details()
    if not action_details:
        return
    action_id = action_details["_id"]
    if "host_file_system" in action_details["jobParams"]:
        work_fs = action_details["jobParams"]["host_file_system"]
        logging.info("host_file_system: %s", work_fs)
    use_gpu = self.get_gpu_config(action_details)
    model_family = action_details["actionDetails"]["modelFamily"]
    self.setup_action_requirements(
        action_details,
        work_fs,
        model_family=model_family,
        action_id=action_id,
    )
    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for export: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "export_log")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    container_name = f"model_export_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(work_fs, use_gpu, action_id=action_id, container_name=container_name)} python3 export.py {self.action_record_id} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "export_log")


@log_errors(raise_exception=False)
def image_build_execute(self: ActionInstance):
    """Execute image building task."""
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details)
    model_family_id = action_details["_idService"]
    action_id = action_details["_id"]
    internal_api_key = self.get_internal_api_key(action_id)
    extra_env_vars = {"MATRICE_INTERNAL_API_KEY": internal_api_key}
    container_name = f"image_build_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(mount_docker_sock=True, extra_env_vars=extra_env_vars, container_name=container_name)} python3 main.py {model_family_id} {action_id}"'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "image_build_log")


@log_errors(raise_exception=False)
def resource_clone_execute(self: ActionInstance):
    """Execute resource clone task."""
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details)
    container_name = f"resource_clone_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(container_name=container_name)} python3 main.py {self.action_record_id} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "resource_clone")


@log_errors(raise_exception=False)
def streaming_gateway_execute(self: ActionInstance):
    """Execute streaming gateway task."""
    action_details = self.get_action_details()
    if not action_details:
        return
    self.setup_action_requirements(action_details)
    if not self.docker_container:
        self.docker_container = (
            f"aiforeveryone/streaming-gateway:{os.environ.get('ENV', 'prod')}"
        )
    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for streaming gateway: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "streaming_gateway")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    container_name = f"streaming_gateway_{self.action_record_id}"
    cmd = f'{self.get_base_docker_cmd(extra_pkgs=["matrice_streaming"], container_name=container_name)} python3 /usr/src/app/streaming_gateway.py {self.action_record_id} "'
    logging.info("cmd is: %s", cmd)
    self.start(cmd, "streaming_gateway")


@log_errors(raise_exception=False)
def kafka_setup_execute(self: ActionInstance):
    """
    Execute kafka server task.
    Kafka runs on port 9092 (SASL_PLAINTEXT) and 9093 (CONTROLLER) - localhost only with --net=host.
    """
    action_details = self.get_action_details()
    if not action_details:
        return
    host_port = self.scaling.get_open_port()
    host_ip = (
        urllib.request.urlopen("https://ident.me", timeout=10).read().decode("utf8")
    )
    # Setup credentials
    self.setup_action_requirements(action_details)

    # Get Docker disk usage to calculate log retention
    from matrice_compute.instance_utils import get_docker_disk_space_usage

    docker_disk_usage = get_docker_disk_space_usage()
    log_retention_bytes = 0
    if docker_disk_usage:
        # Calculate 90% of total Docker disk space in bytes
        available_disk_gb = docker_disk_usage["available"]
        log_retention_bytes = int(
            available_disk_gb * 0.9 * 1024 * 1024 * 1024
        )  # Convert GB to bytes
        logging.info(
            "Kafka log retention set to %d bytes (90%% of %f GB Docker disk)",
            log_retention_bytes,
            available_disk_gb,
        )
    else:
        # Fallback if Docker disk usage cannot be determined
        log_retention_bytes = 500 * 1024 * 1024 * 1024  # 10GB default
        logging.warning(
            "Could not determine Docker disk usage, using default 10GB log retention"
        )

    # Prepare environment variables for Kafka
    env = os.environ.get("ENV", "prod")
    env_vars = {
        "ENV": env,
        "MATRICE_SECRET_ACCESS_KEY": self.matrice_secret_access_key,
        "MATRICE_ACCESS_KEY_ID": self.matrice_access_key_id,
        "KAFKA_NODE_ID": 1,
        "KAFKA_PROCESS_ROLES": "broker,controller",
        "KAFKA_LISTENERS": "SASL_PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093",
        "KAFKA_ADVERTISED_LISTENERS": f"SASL_PLAINTEXT://{host_ip}:{host_port}",
        "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "CONTROLLER:PLAINTEXT,SASL_PLAINTEXT:SASL_PLAINTEXT",
        "KAFKA_CONTROLLER_LISTENER_NAMES": "CONTROLLER",
        "KAFKA_CONTROLLER_QUORUM_VOTERS": "1@localhost:9093",
        "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": 1,
        "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": 1,
        "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": 1,
        "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS": 0,
        "KAFKA_NUM_PARTITIONS": 5,
        "KAFKA_SASL_ENABLED_MECHANISMS": "SCRAM-SHA-256",
        "KAFKA_SASL_MECHANISM_INTER_BROKER_PROTOCOL": "SCRAM-SHA-256",
        "KAFKA_INTER_BROKER_LISTENER_NAME": "SASL_PLAINTEXT",
        "KAFKA_MESSAGE_MAX_BYTES": 25000000,
        "KAFKA_HEAP_OPTS": "-Xms2G -Xmx8G",
        "KAFKA_NUM_NETWORK_THREADS": 6,
        "KAFKA_NUM_IO_THREADS": 8,
        "KAFKA_REPLICA_FETCH_MAX_BYTES": 25000000,
        "KAFKA_FETCH_MESSAGE_MAX_BYTES": 25000000,
        "KAFKA_REPLICA_FETCH_RESPONSE_MAX_BYTES": 25000000,
        "KAFKA_REPLICA_FETCH_RESPONSE_MAX_BYTES": 25000000,
        # Log retention settings based on Docker disk space
        "KAFKA_LOG_RETENTION_BYTES": log_retention_bytes,
        "KAFKA_LOG_SEGMENT_BYTES": min(
            1073741824, log_retention_bytes // 10
        ),  # 1GB or 10% of retention, whichever is smaller
    }

    # Build environment variable command parts
    env_args = " ".join(
        [f"-e {key}={shlex.quote(str(value))}" for key, value in env_vars.items()]
    )

    # Build the docker command with --net=host
    pypi_index = f"https://{'test.' if env != 'prod' else ''}pypi.org/simple/"

    if env == 'dev':
        pypi_index = f"https://test.pypi.org/simple/ --pre"
        pkgs = f"matrice_common>=1.0.0 matrice>=1.0.0"
    else:
        pkgs = f"matrice_common matrice"

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for kafka: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "kafka_setup")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    # Kafka container with --net=host (Ports: 9092, 9093)
    cmd = (
        f"docker run --net=host "
        f"{env_args} "
        f"--shm-size=30G --pull=always "
        f'aiforeveryone/matrice-kafka:latest /bin/bash -c "'
        f"cd /opt/kafka/bin && "
        f"source venv/bin/activate && "
        f"/opt/kafka/bin/startup.sh & "
        f"if [ -f requirements.txt ]; then venv/bin/python3 -m pip install -r requirements.txt; fi && "
        f"venv/bin/python3 -m pip install --upgrade --force-reinstall --index-url {pypi_index} {pkgs} && "
        f"sleep 20 && "
        f'venv/bin/python3 main.py {self.action_record_id} {host_port}"'
    )

    logging.info("Starting Kafka container (Ports: 9092, 9093): %s", cmd)
    self.start(cmd, "kafka_setup")


@log_errors(raise_exception=False)
def inference_tracker_setup_execute(self: ActionInstance):

    """
    Creates and start inference tracker.
    Inference tracker runs on port 8110 (localhost only with --net=host).
    """ 
    
    action_details = self.get_action_details()
    if not action_details:
        return
    
    image = self.docker_container
    
    self.setup_action_requirements(action_details)

    existing_container_id = action_details["actionDetails"].get("containerId")
    if existing_container_id:
        # Check if container actually exists before trying to restart
        if ActionInstance.container_exists(existing_container_id):
            logging.info(
                "Using existing container ID for inference tracker: %s",
                existing_container_id,
            )
            self.docker_container = existing_container_id
            cmd = "docker restart " + self.docker_container
            self.start(cmd, "inference_tracker_setup")
            return
        else:
            logging.warning(
                "Container %s not found. Creating new container.",
                existing_container_id
            )
            # Fall through to create new container

    # This is the existing Docker run command
    container_name = f"inference_tracker_{self.action_record_id}"
    worker_cmd = (
        f"docker run -d --pull=always --net=host "
        f"--cidfile ./{self.action_record_id}.cid "
        f"--name {container_name} "
        f"-v matrice_myvol:/matrice_data "
        f'-e ENV="{os.environ.get("ENV", "prod")}" '
        f'-e MATRICE_SECRET_ACCESS_KEY="{self.matrice_secret_access_key}" '
        f'-e MATRICE_ACCESS_KEY_ID="{self.matrice_access_key_id}" '
        f'-e ACTION_ID="{self.action_record_id}" '
        f"{image}"
    )
    
    self.start(worker_cmd, "inference_tracker_setup")