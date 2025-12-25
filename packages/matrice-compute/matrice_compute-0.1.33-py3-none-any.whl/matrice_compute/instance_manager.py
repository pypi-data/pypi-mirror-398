"""Module providing instance_manager functionality."""

import json
import logging
import os
import subprocess
import threading
import time
from kafka import KafkaProducer
from matrice_compute.actions_manager import ActionsManager
from matrice_compute.actions_scaledown_manager import ActionsScaleDownManager
from matrice_compute.compute_operations_handler import ComputeOperationsHandler
from matrice_compute.instance_utils import (
    get_instance_info,
    get_decrypted_access_key_pair,
)
from matrice_compute.resources_tracker import (
    MachineResourcesTracker,
    ActionsResourcesTracker,
    KafkaResourceMonitor,
)
from matrice_compute.scaling import Scaling
from matrice_compute.shutdown_manager import ShutdownManager
from matrice_common.session import Session
from matrice_common.utils import log_errors


class InstanceManager:
    """Class for managing compute instances and their associated actions.

    Now includes auto streaming capabilities for specified deployment IDs.
    """

    def __init__(
        self,
        matrice_access_key_id: str = "",
        matrice_secret_access_key: str = "",
        encryption_key: str = "",
        instance_id: str = "",
        service_provider: str = "",
        env: str = "",
        gpus: str = "",
        workspace_dir: str = "matrice_workspace",
        enable_kafka: bool = False,
    ):
        """Initialize an instance manager.

        Args:
            matrice_access_key_id (str): Access key ID for Matrice authentication.
                Defaults to empty string.
            matrice_secret_access_key (str): Secret access key for Matrice
                authentication. Defaults to empty string.
            encryption_key (str): Key used for encrypting sensitive data.
                Defaults to empty string.
            instance_id (str): Unique identifier for this compute instance.
                Defaults to empty string.
            service_provider (str): Cloud service provider being used.
                Defaults to empty string.
            env (str): Environment name (e.g. dev, prod).
                Defaults to empty string.
            gpus (str): GPU configuration string (e.g. "0,1").
                Defaults to empty string.
            workspace_dir (str): Directory for workspace files.
                Defaults to "matrice_workspace".
            enable_kafka (bool): Enable Kafka communication (default False).
        """
        self.session = self._setup_env_credentials(
            env,
            service_provider,
            instance_id,
            encryption_key,
            matrice_access_key_id,
            matrice_secret_access_key,
        )
        os.environ["WORKSPACE_DIR"] = str(workspace_dir)
        os.environ["GPUS"] = json.dumps(gpus)
        self.scaling = Scaling(
            self.session,
            os.environ.get("INSTANCE_ID"),
            enable_kafka,
        )
        logging.info("InstanceManager initialized with scaling")
        jupyter_token = os.environ.get("JUPYTER_TOKEN")
        if jupyter_token:
            self.scaling.update_jupyter_token(jupyter_token)
            logging.info("InstanceManager updated Jupyter token")
        else:
            logging.warning("No Jupyter token found in environment variables")
        self.current_actions = {}
        self.actions_manager = ActionsManager(self.scaling)
        logging.info("InstanceManager initialized with actions manager")
        self.scale_down_manager = ActionsScaleDownManager(self.scaling)
        logging.info("InstanceManager initialized with scale down manager")
        self.shutdown_manager = ShutdownManager(self.scaling)
        logging.info("InstanceManager initialized with shutdown manager")
        self.machine_resources_tracker = MachineResourcesTracker(self.scaling)
        logging.info("InstanceManager initialized with machine resources tracker")
        self.actions_resources_tracker = ActionsResourcesTracker(self.scaling)
        logging.info("InstanceManager initialized with actions resources tracker")

        # Initialize Kafka resource monitor using the same internal Kafka as scaling
        try:
            kafka_bootstrap = self.scaling.get_kafka_bootstrap_servers()
            self.kafka_resource_monitor = KafkaResourceMonitor(
                instance_id=os.environ.get("INSTANCE_ID"),
                kafka_bootstrap=kafka_bootstrap,
                interval_seconds=60
            )
            logging.info("InstanceManager initialized with Kafka resource monitor using internal Kafka: %s", kafka_bootstrap)
        except (ValueError, Exception) as e:
            logging.warning("Failed to initialize Kafka resource monitor: %s", e)
            self.kafka_resource_monitor = None

        # Initialize Compute Operations Handler for event-driven operations
        # Uses EventListener from matrice_common for simplified Kafka consumption
        try:
            instance_id = os.environ.get("INSTANCE_ID")
            self.compute_operations_handler = ComputeOperationsHandler(
                actions_manager=self.actions_manager,
                session=self.session,
                scaling=self.scaling,
                instance_id=instance_id
            )
            logging.info("InstanceManager initialized with Compute Operations Handler for instance ID: %s", instance_id)
        except (ValueError, Exception) as e:
            logging.warning("Failed to initialize Compute Operations Handler: %s", e)
            self.compute_operations_handler = None

        self.poll_interval = 10
        # Note: encryption_key is set in _setup_env_credentials
        
        # Initialize container monitoring
        self.container_monitor_thread = None
        self.container_monitor_running = False
        self.container_kafka_producer = None
        
        logging.info("InstanceManager initialized.")

        # report the resources at startup
        try:
            self.scaling.report_architecture_info()
            logging.info("InstanceManager reported initial resources.")
        except Exception as exc:
            logging.error(
                "Error reporting initial resources: %s",
                str(exc),
            )

    @log_errors(default_return=None, raise_exception=True, log_error=True)
    def _setup_env_credentials(
        self,
        env: str,
        service_provider: str,
        instance_id: str,
        encryption_key: str,
        matrice_access_key_id: str,
        matrice_secret_access_key: str,
    ):
        """Set up environment credentials.

        Args:
            env (str): Environment name
            service_provider (str): Cloud service provider
            instance_id (str): Instance identifier
            encryption_key (str): Encryption key
            matrice_access_key_id (str): Matrice access key ID
            matrice_secret_access_key (str): Matrice secret access key

        Returns:
            Session: Initialized session object

        Raises:
            Exception: If required environment variables are not set
        """
        try:
            auto_instance_info = get_instance_info(service_provider, instance_id)
            (
                auto_service_provider,
                auto_instance_id,
            ) = auto_instance_info
        except Exception as exc:
            logging.error(
                "Error getting instance info: %s",
                str(exc),
            )
            auto_service_provider = ""
            auto_instance_id = ""

        manual_instance_info = {
            "ENV": env or os.environ.get("ENV"),
            "SERVICE_PROVIDER": service_provider
            or os.environ.get("SERVICE_PROVIDER")
            or auto_service_provider,
            "INSTANCE_ID": instance_id
            or os.environ.get("INSTANCE_ID")
            or auto_instance_id,
            "MATRICE_ENCRYPTION_KEY": encryption_key
            or os.environ.get("MATRICE_ENCRYPTION_KEY"),
            "MATRICE_ACCESS_KEY_ID": matrice_access_key_id
            or os.environ.get("MATRICE_ACCESS_KEY_ID"),
            "MATRICE_SECRET_ACCESS_KEY": matrice_secret_access_key
            or os.environ.get("MATRICE_SECRET_ACCESS_KEY"),
        }
        for (
            key,
            value,
        ) in manual_instance_info.items():
            if value is not None:
                os.environ[key] = str(value)
        if not (os.environ.get("SERVICE_PROVIDER") and os.environ.get("INSTANCE_ID")):
            raise Exception(
                "SERVICE_PROVIDER and INSTANCE_ID must be set as environment variables or passed as arguments"
            )
        self.encryption_key = manual_instance_info["MATRICE_ENCRYPTION_KEY"]

        access_key = manual_instance_info["MATRICE_ACCESS_KEY_ID"]
        secret_key = manual_instance_info["MATRICE_SECRET_ACCESS_KEY"]

        if (  # Keys are not encrypted
            self.encryption_key
            and access_key
            and secret_key
            and len(access_key) != 21
            and len(secret_key) != 21
        ):
            access_key, secret_key = self._decrypt_access_key_pair(
                access_key,
                secret_key,
                self.encryption_key,
            )
        os.environ["MATRICE_SECRET_ACCESS_KEY"] = secret_key
        os.environ["MATRICE_ACCESS_KEY_ID"] = access_key
        os.environ["MATRICE_ENCRYPTION_KEY"] = self.encryption_key
        return Session(
            account_number="",
            secret_key=secret_key,
            access_key=access_key,
        )

    @log_errors(default_return=(None, None), raise_exception=False)
    def _decrypt_access_key_pair(
        self,
        enc_access_key: str,
        enc_secret_key: str,
        encryption_key: str = "",
    ) -> tuple:
        """Decrypt the access key pair.

        Args:
            enc_access_key (str): Encrypted access key
            enc_secret_key (str): Encrypted secret key
            encryption_key (str): Key for decryption. Defaults to empty string.

        Returns:
            tuple: Decrypted (access_key, secret_key) pair
        """
        return get_decrypted_access_key_pair(
            enc_access_key,
            enc_secret_key,
            encryption_key,
        )

    @log_errors(raise_exception=True, log_error=True)
    def start_instance_manager(self) -> None:
        """Run the instance manager loop."""
        while True:
            try:
                self.shutdown_manager.handle_shutdown(
                    bool(self.actions_manager.get_current_actions())
                )
            except Exception as exc:
                logging.error(
                    "Error in shutdown_manager handle_shutdown: %s",
                    str(exc),
                )
            # try:
            #     self.scale_down_manager.auto_scaledown_actions()
            # except Exception as exc:
            #     logging.error(
            #         "Error in scale_down_manager auto_scaledown_actions: %s",
            #         str(exc),
            #     )
            # try:
            #     self.machine_resources_tracker.update_available_resources()
            # except Exception as exc:
            #     logging.error(
            #         "Error in machine_resources_tracker update_available_resources: %s",
            #         str(exc),
            #     )
            try:
                self.actions_resources_tracker.update_actions_resources()
            except Exception as exc:
                logging.error(
                    "Error in actions_resources_tracker update_actions_resources: %s",
                    str(exc),
                )

            time.sleep(self.poll_interval)

    @log_errors(raise_exception=False, log_error=True)
    def start_container_status_monitor(self):
        """Start the background container status monitoring."""
        if self.container_monitor_running:
            logging.info("Container status monitor is already running")
            return
        
        self.container_monitor_running = True
        self.container_monitor_thread = threading.Thread(
            target=self._container_status_monitor_worker,
            daemon=True,
            name="ContainerStatusMonitor"
        )
        self.container_monitor_thread.start()
        logging.info("Started container status monitoring thread")

    @log_errors(raise_exception=False, log_error=True)
    def stop_container_status_monitor(self):
        """Stop the background container status monitoring."""
        if not self.container_monitor_running:
            return
        
        logging.info("Stopping container status monitor...")
        self.container_monitor_running = False
        
        if self.container_monitor_thread:
            self.container_monitor_thread.join(timeout=10)
        
        if self.container_kafka_producer:
            self.container_kafka_producer.close()
            self.container_kafka_producer = None
        
        logging.info("Container status monitor stopped")

    def _container_status_monitor_worker(self):
        """Background worker function that monitors container status."""
        # Initialize Kafka producer
        try:
            if self.scaling.enable_kafka:
                bootstrap_servers = self.scaling.get_kafka_bootstrap_servers()
                self.container_kafka_producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    max_block_ms=5000  # Timeout if Kafka is down
                )
                logging.info("Container status monitor: Kafka producer initialized")
            else:
                logging.warning("Container status monitor: Kafka is disabled, no monitoring will be performed")
                return
        except Exception as e:
            logging.error("Container status monitor: Failed to initialize Kafka producer: %s", str(e))
            return
        
        instance_id = os.environ.get("INSTANCE_ID")
        topic_name = "compute_container_status"
        
        logging.info("Container status monitor started for instance: %s", instance_id)
        
        while self.container_monitor_running:
            try:
                # Get container status using docker ps -a
                result = subprocess.run(
                    ["docker", "ps", "-a", "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    logging.error("Container status monitor: docker ps command failed: %s", result.stderr)
                    time.sleep(30)  # Wait before retrying
                    continue
                
                # Parse container information
                containers = []
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        try:
                            container_info = json.loads(line)
                            containers.append({
                                "container_id": container_info.get("ID", ""),
                                "image": container_info.get("Image", ""),
                                "command": container_info.get("Command", ""),
                                "created": container_info.get("CreatedAt", ""),
                                "status": container_info.get("Status", ""),
                                "ports": container_info.get("Ports", ""),
                                "names": container_info.get("Names", ""),
                                "size": container_info.get("Size", ""),
                                "state": container_info.get("State", ""),
                                "labels": container_info.get("Labels", "")
                            })
                        except json.JSONDecodeError as e:
                            logging.warning("Container status monitor: Failed to parse container info: %s", str(e))
                            continue
                
                # Prepare message for Kafka
                status_message = {
                    "timestamp": time.time(),
                    "instance_id": instance_id,
                    "container_count": len(containers),
                    "containers": containers
                }
                
                # Send to Kafka
                if self.container_kafka_producer:
                    try:
                        self.container_kafka_producer.send(topic_name, status_message)
                        logging.info("Container status monitor: Sent status for %d containers", len(containers))
                    except Exception as e:
                        logging.error("Container status monitor: Failed to send to Kafka: %s", str(e))
                
            except subprocess.TimeoutExpired:
                logging.error("Container status monitor: docker ps command timed out")
            except Exception as e:
                logging.error("Container status monitor: Unexpected error: %s", str(e))
            
            # Wait 30 seconds before next check
            for _ in range(30):
                if not self.container_monitor_running:
                    break
                time.sleep(1)
        
        logging.info("Container status monitor worker stopped")

    @log_errors(default_return=(None, None), raise_exception=True)
    def start(self) -> tuple:
        """Start the instance manager threads.

        Returns:
            tuple: (instance_manager_thread, actions_manager_thread)
        """
        # Start Kafka resource monitor in background thread
        if self.kafka_resource_monitor:
            try:
                self.kafka_resource_monitor.start()
                logging.info("Started Kafka resource monitor")
            except Exception as exc:
                logging.error("Failed to start Kafka resource monitor: %s", str(exc))

        # Start Compute Operations Handler in background thread
        if self.compute_operations_handler:
            try:
                self.compute_operations_handler.start()
                logging.info("Started Compute Operations Handler")
            except Exception as exc:
                logging.error("Failed to start Compute Operations Handler: %s", str(exc))

        # Start Container Status Monitor in background thread
        try:
            self.start_container_status_monitor()
            logging.info("Started Container Status Monitor")
        except Exception as exc:
            logging.error("Failed to start Container Status Monitor: %s", str(exc))

        # Create and start threads
        instance_manager_thread = threading.Thread(
            target=self.start_instance_manager,
            name="InstanceManager",
        )
        instance_manager_thread.start()

        actions_manager_thread = threading.Thread(
            target=self.actions_manager.start_actions_manager,
            name="ActionsManager",
        )
        actions_manager_thread.start()

        return (
            instance_manager_thread,
            actions_manager_thread,
        )
