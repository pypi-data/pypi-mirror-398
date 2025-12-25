

import os
import logging
import json
import psutil
from matrice_common.utils import log_errors
from kafka import KafkaProducer, KafkaConsumer
import uuid
import time
import base64
import threading
import platform
import subprocess


class Scaling:

    """Class providing scaling functionality for compute instances."""

    def __init__(self, session, instance_id=None, enable_kafka=False):
        """Initialize Scaling instance.

        Args:
            session: Session object for making RPC calls
            instance_id: ID of the compute instance
            enable_kafka: Enable Kafka communication (default True)

        Raises:
            Exception: If instance_id is not provided
        """
        if not instance_id:
            msg = "Instance id not set for this instance. Cannot perform the operation for job-scheduler without instance id"
            logging.error(msg)
            raise ValueError(msg)
        self.instance_id = instance_id
        self.session = session
        self.rpc = session.rpc
        used_ports_str = os.environ.get("USED_PORTS", "")
        self.used_ports = set(int(p) for p in used_ports_str.split(",") if p.strip())

        # Kafka configuration and initialization
        self.enable_kafka = enable_kafka
        self.kafka_producer = None
        self.kafka_consumer = None
        self.kafka_thread = None
        self.kafka_running = False

        # Maps correlation_id to threading.Event for request/response matching
        self.pending_requests = {}
        # Maps correlation_id to response data
        self.response_map = {}
        self.response_lock = threading.Lock()

        if self.enable_kafka:
            try:
                self.kafka_config = {
                    "bootstrap_servers": self.get_kafka_bootstrap_servers(),
                    "action_request_topic": "action_requests",
                    "action_response_topic": "action_responses",
                    "compute_request_topic": "compute_requests",
                    "compute_response_topic": "compute_responses"
                }

                # Initialize single producer
                self.kafka_producer = KafkaProducer(
                    bootstrap_servers=self.kafka_config["bootstrap_servers"],
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    max_block_ms=5000  # Timeout if Kafka is down
                )

                # Initialize single consumer for both response topics
                self.kafka_consumer = KafkaConsumer(
                    self.kafka_config["action_response_topic"],
                    self.kafka_config["compute_response_topic"],
                    bootstrap_servers=self.kafka_config["bootstrap_servers"],
                    group_id=f"py_compute_{instance_id}",
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    consumer_timeout_ms=1000,  # Poll timeout
                    session_timeout_ms=60000,  # Increase session timeout to 60s (default 30s)
                    heartbeat_interval_ms=3000,  # Send heartbeat every 3s
                    max_poll_interval_ms=300000  # Max time between polls: 5 minutes
                )

                # Start background thread to handle responses
                self.kafka_running = True
                self.kafka_thread = threading.Thread(target=self._kafka_response_listener, daemon=True)
                self.kafka_thread.start()

                logging.info(f"Kafka enabled with bootstrap servers: {self.kafka_config['bootstrap_servers']}")
            except Exception as e:
                logging.warning(f"Failed to initialize Kafka, will use REST API only: {e}")
                self.enable_kafka = False
                self.kafka_producer = None
                self.kafka_consumer = None

        logging.info(
            "Initialized Scaling with instance_id: %s, Kafka enabled: %s",
            instance_id,
            self.enable_kafka
        )

    @log_errors(default_return=None, log_error=True)
    def get_kafka_bootstrap_servers(self):
        """Get Kafka bootstrap servers from API and decode base64 fields.

        Returns:
            str: Kafka bootstrap servers in format "ip:port"

        Raises:
            ValueError: If unable to fetch Kafka configuration
        """
        path = "/v1/actions/get_kafka_info"
        response = self.rpc.get(path=path)
        if not response or not response.get("success"):
            raise ValueError(f"Failed to fetch Kafka config: {response.get('message', 'No response')}")
        encoded_ip = response["data"]["ip"]
        encoded_port = response["data"]["port"]
        ip = base64.b64decode(encoded_ip).decode("utf-8")
        port = base64.b64decode(encoded_port).decode("utf-8")
        bootstrap_servers = f"{ip}:{port}"
        # logging.info(f"Retrieved Kafka bootstrap servers: {bootstrap_servers}")
        return bootstrap_servers

    @log_errors(default_return=(None, "Error processing response", "Response processing failed"), log_error=True)
    def handle_response(self, resp, success_message, error_message):
        """Helper function to handle API response.

        Args:
            resp: Response from API call
            success_message: Message to log on success
            error_message: Message to log on error

        Returns:
            Tuple of (data, error, message)
        """
        if resp.get("success"):
            data = resp.get("data")
            error = None
            message = success_message
            logging.info(message)
        else:
            data = resp.get("data")
            error = resp.get("message")
            message = error_message
            logging.error("%s: %s", message, error)
        return data, error, message

    def _kafka_response_listener(self):
        """
        Background thread that continuously polls for Kafka responses.

        This thread runs in the background and listens for responses from both
        action_responses and compute_responses topics. When a response is received,
        it matches the correlation ID to pending requests and wakes up the waiting thread.
        """
        logging.info("Kafka response listener thread started")

        while self.kafka_running:
            try:
                # Poll for messages with 1 second timeout
                message_batch = self.kafka_consumer.poll(timeout_ms=1000)

                if message_batch:
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            try:
                                msg = message.value
                                correlation_id = msg.get("correlationId")

                                if correlation_id:
                                    with self.response_lock:
                                        if correlation_id in self.pending_requests:
                                            # Store response and signal waiting thread
                                            self.response_map[correlation_id] = msg
                                            self.pending_requests[correlation_id].set()
                                            logging.debug(f"Received Kafka response for correlation_id: {correlation_id}")
                                else:
                                    logging.warning(f"Received Kafka message without correlationId: {msg}")
                            except Exception as e:
                                logging.error(f"Error processing Kafka message: {e}")

            except Exception as e:
                if self.kafka_running:  # Only log if not shutting down
                    logging.error(f"Error in Kafka response listener: {e}")
                    time.sleep(1)  # Avoid tight loop on persistent errors

        logging.info("Kafka response listener thread stopped")

    def _send_kafka_request(self, api, payload, request_topic, response_topic, timeout=5):
        """
        Send a request via Kafka and wait for response using the persistent consumer.

        Args:
            api: API name to call
            payload: Request payload dictionary
            request_topic: Kafka topic to send request to
            response_topic: Kafka topic to receive response from (not used, kept for signature)
            timeout: Timeout in seconds to wait for response

        Returns:
            Tuple of (data, error, message, kafka_success)
            kafka_success is True if response received, False if timeout/error
        """
        if not self.enable_kafka or not self.kafka_producer:
            return None, "Kafka not enabled", "Kafka not available", False

        correlation_id = str(uuid.uuid4())
        request_message = {
            "correlationId": correlation_id,
            "api": api,
            "payload": payload,
        }

        # Create event for this request
        event = threading.Event()

        with self.response_lock:
            self.pending_requests[correlation_id] = event

        try:
            # Add auth token if available
            headers = None
            if hasattr(self.session.rpc, 'AUTH_TOKEN'):
                self.session.rpc.AUTH_TOKEN.set_bearer_token()
                auth_token = self.session.rpc.AUTH_TOKEN.bearer_token
                auth_token = auth_token.replace("Bearer ", "")
                headers = [("Authorization", bytes(f"{auth_token}", "utf-8"))]

            # Send request
            self.kafka_producer.send(request_topic, request_message, headers=headers)
            logging.info(f"Sent Kafka request for {api} with correlation_id: {correlation_id}")

            # Wait for response with timeout
            if event.wait(timeout=timeout):
                # Response received
                with self.response_lock:
                    response = self.response_map.pop(correlation_id, None)
                    self.pending_requests.pop(correlation_id, None)

                if response:
                    if response.get("status") == "success":
                        data = response.get("data")
                        logging.info(f"Kafka success for {api}")
                        return data, None, f"Fetched via Kafka for {api}", True
                    else:
                        error = response.get("error", "Unknown error")
                        logging.error(f"Kafka error response for {api}: {error}")
                        return None, error, f"Kafka error response for {api}", True
                else:
                    logging.warning(f"Kafka response received but missing data for {api}")
                    return None, "Response missing data", "Kafka response error", False
            else:
                # Timeout
                with self.response_lock:
                    self.pending_requests.pop(correlation_id, None)
                logging.warning(f"Kafka response timeout for {api} after {timeout} seconds")
                return None, "Kafka response timeout", "Kafka response timeout", False

        except Exception as e:
            # Cleanup on error
            with self.response_lock:
                self.pending_requests.pop(correlation_id, None)
            logging.error(f"Kafka send error for {api}: {e}")
            return None, f"Kafka error: {e}", "Kafka send failed", False

    def _hybrid_request(self, api, payload, request_topic, response_topic, rest_fallback_func):
        """
        Hybrid request method: try Kafka first, fallback to REST, cache if both fail.

        Args:
            api: API name
            payload: Request payload
            request_topic: Kafka request topic
            response_topic: Kafka response topic
            rest_fallback_func: Function to call for REST fallback (should return same format as handle_response)

        Returns:
            Tuple of (data, error, message) matching the API response pattern
        """
        # Try Kafka first
        if self.enable_kafka:
            data, error, message, kafka_success = self._send_kafka_request(
                api, payload, request_topic, response_topic, timeout=5
            )

            if kafka_success and error is None:
                # Kafka succeeded
                return data, error, message

            # Kafka returned an error response (not transport error)
            if kafka_success and error is not None:
                logging.warning(f"Kafka returned error for {api}, falling back to REST")

        # Kafka failed or disabled, try REST
        logging.debug(f"Using REST API for {api}")
        try:
            rest_response = rest_fallback_func()

            # Return REST response (success or failure)
            if rest_response and len(rest_response) == 3:
                return rest_response
            else:
                # Unexpected REST response format
                logging.error(f"REST API returned unexpected format for {api}")
                return None, "Unexpected REST response format", "REST API error"

        except Exception as e:
            # REST failed
            logging.error(f"REST API failed for {api}: {e}")
            return None, str(e), "REST API failed"

    def shutdown(self):
        """Gracefully shutdown Kafka connections."""
        if self.kafka_running:
            logging.info("Shutting down Kafka connections...")
            self.kafka_running = False

            if self.kafka_thread:
                self.kafka_thread.join(timeout=5)

            if self.kafka_consumer:
                self.kafka_consumer.close()

            if self.kafka_producer:
                self.kafka_producer.close()

            logging.info("Kafka connections closed")

    @log_errors(log_error=True)
    def get_downscaled_ids(self):
        """Get IDs of downscaled instances using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Getting downscaled ids for instance %s", self.instance_id)

        payload = {"instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/compute/down_scaled_ids/{self.instance_id}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Downscaled ids info fetched successfully",
                "Could not fetch the Downscaled ids info",
            )

        return self._hybrid_request(
            api="get_downscaled_ids",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(default_return=(None, "API call failed", "Failed to stop instance"), log_error=True)
    def stop_instance(self):
        """Stop the compute instance using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Stopping instance %s", self.instance_id)

        payload = {
            "_idInstance": self.instance_id,
            "isForcedStop": False,
        }

        def rest_fallback():
            path = "/v1/compute/compute_instance/stop"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Instance stopped successfully",
                "Could not stop the instance",
            )

        return self._hybrid_request(
            api="stop_instance",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )
    
    @log_errors(log_error=True)
    def update_jupyter_token(self, token=""):
        """Update Jupyter notebook token using Kafka (with REST fallback)."""
        payload = {"token": token, "instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/compute/update_jupyter_notebook_token/{self.instance_id}"
            resp = self.rpc.put(path=path, payload={"token": token})
            return self.handle_response(
                resp,
                "Resources updated successfully",
                "Could not update the resources",
            )

        return self._hybrid_request(
            api="update_jupyter_token",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def update_action_status(
        self,
        service_provider="",
        action_record_id="",
        isRunning=True,
        status="",
        docker_start_time=None,
        action_duration=0,
        cpuUtilisation=0.0,
        gpuUtilisation=0.0,
        memoryUtilisation=0.0,
        gpuMemoryUsed=0,
        createdAt=None,
        updatedAt=None,
    ):
        """Update status of an action using Kafka (with REST fallback).

        Args:
            service_provider: Provider of the service
            action_record_id: ID of the action record
            isRunning: Whether action is running
            status: Status of the action
            docker_start_time: Start time of docker container
            action_duration: Duration of the action
            cpuUtilisation: CPU utilization percentage
            gpuUtilisation: GPU utilization percentage
            memoryUtilisation: Memory utilization percentage
            gpuMemoryUsed: GPU memory used
            createdAt: Creation timestamp
            updatedAt: Last update timestamp

        Returns:
            Tuple of (data, error, message) from API response
        """
        if not action_record_id:
            return None, "Action record id is required", "Action record id is required"

        logging.info("Updating action status for action %s", action_record_id)

        payload = {
            "instanceID": self.instance_id,
            "serviceProvider": service_provider,
            "actionRecordId": action_record_id,
            "isRunning": isRunning,
            "status": status,
            "dockerContainerStartTime": docker_start_time,
            "cpuUtilisation": cpuUtilisation,
            "gpuUtilisation": gpuUtilisation,
            "memoryUtilisation": memoryUtilisation,
            "gpuMemoryUsed": gpuMemoryUsed,
            "actionDuration": action_duration,
            "createdAt": createdAt,
            "updatedAt": updatedAt,
        }

        def rest_fallback():
            path = "/v1/compute/update_action_status"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Action status details updated successfully",
                "Could not update the action status details ",
            )

        return self._hybrid_request(
            api="update_action_status",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def update_status(
        self,
        action_record_id,
        action_type,
        service_name,
        stepCode,
        status,
        status_description,
    ):
        """Update status of an action using Kafka (with REST fallback).

        Args:
            action_record_id: ID of the action record
            action_type: Type of action
            service_name: Name of the service
            stepCode: Code indicating step in process
            status: Status to update
            status_description: Description of the status
        """
        logging.info("Updating status for action %s", action_record_id)

        payload = {
            "_id": action_record_id,
            "action": action_type,
            "serviceName": service_name,
            "stepCode": stepCode,
            "status": status,
            "statusDescription": status_description,
        }

        def rest_fallback():
            url = "/v1/actions"
            self.rpc.put(path=url, payload=payload)
            return None, None, "Status updated"

        return self._hybrid_request(
            api="update_action",
            payload=payload,
            request_topic=self.kafka_config["action_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["action_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def get_shutdown_details(self):
        """Get shutdown details for the instance using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Getting shutdown details for instance %s", self.instance_id)

        payload = {"instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/compute/get_shutdown_details/{self.instance_id}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Shutdown info fetched successfully",
                "Could not fetch the shutdown details",
            )

        return self._hybrid_request(
            api="get_shutdown_details",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def get_tasks_details(self):
        """Get task details for the instance using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Getting tasks details for instance %s", self.instance_id)

        payload = {"instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/actions/fetch_instance_action_details/{self.instance_id}/action_details"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Task details fetched successfully",
                "Could not fetch the task details",
            )

        return self._hybrid_request(
            api="get_tasks_details",
            payload=payload,
            request_topic=self.kafka_config["action_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["action_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def get_action_details(self, action_status_id):
        """Get details for a specific action using Kafka (with REST fallback).

        Args:
            action_status_id: ID of the action status to fetch

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Getting action details for action %s", action_status_id)

        payload = {"actionRecordId": action_status_id}

        def rest_fallback():
            path = f"/v1/actions/action/{action_status_id}/details"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Task details fetched successfully",
                "Could not fetch the task details",
            )

        return self._hybrid_request(
            api="get_action_details",
            payload=payload,
            request_topic=self.kafka_config["action_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["action_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def update_action(
        self,
        id="",
        step_code="",
        action_type="",
        status="",
        sub_action="",
        status_description="",
        service="",
        job_params=None,
    ):
        """Update an action using Kafka (with REST fallback).

        Args:
            id: Action ID
            step_code: Step code
            action_type: Type of action
            status: Status of the action
            sub_action: Sub-action details
            status_description: Description of the status
            service: Service name
            job_params: Job parameters dictionary

        Returns:
            Tuple of (data, error, message) from API response
        """
        if job_params is None:
            job_params = {}

        logging.info("Updating action %s", id)

        payload = {
            "_id": id,
            "stepCode": step_code,
            "action": action_type,
            "status": status,
            "subAction": sub_action,
            "statusDescription": status_description,
            "serviceName": service,
            "jobParams": job_params,
        }

        def rest_fallback():
            path = "/v1/actions"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Error logged successfully",
                "Could not log the errors",
            )

        return self._hybrid_request(
            api="update_action",
            payload=payload,
            request_topic=self.kafka_config["action_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["action_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )
           

    @log_errors(log_error=True)
    def assign_jobs(self, is_gpu):
        """Assign jobs to the instance using REST API.

        Args:
            is_gpu: Boolean or any value indicating if this is a GPU instance.
                    Will be converted to proper boolean.

        Returns:
            Tuple of (data, error, message) from API response
        """
        # Convert is_gpu to proper boolean
        is_gpu_bool = bool(is_gpu)
        logging.info("Assigning jobs for instance %s (GPU: %s)", self.instance_id, is_gpu_bool)

        # Use REST API directly
        is_gpu_str = str(is_gpu_bool).lower()
        path = f"/v1/actions/assign_jobs/{is_gpu_str}/{self.instance_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Pinged successfully",
            "Could not ping the scaling jobs",
        )
          

    @log_errors(log_error=True)
    def update_available_resources(
        self,
        availableCPU=0,
        availableGPU=0,
        availableMemory=0,
        availableGPUMemory=0,
    ):
        """Update available resources for the instance using Kafka (with REST fallback).

        Args:
            availableCPU: Available CPU resources
            availableGPU: Available GPU resources
            availableMemory: Available memory
            availableGPUMemory: Available GPU memory

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Updating available resources for instance %s", self.instance_id)
        payload = {
            "instance_id": self.instance_id,
            "availableMemory": availableMemory,
            "availableCPU": availableCPU,
            "availableGPUMemory": availableGPUMemory,
            "availableGPU": availableGPU,
        }

        # Define REST fallback function
        def rest_fallback():
            path = f"/v1/compute/update_available_resources/{self.instance_id}"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Resources updated successfully",
                "Could not update the resources",
            )

        # Use hybrid approach: Kafka first, REST fallback, cache if both fail
        return self._hybrid_request(
            api="update_available_resources",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def update_action_docker_logs(self, action_record_id, log_content):
        """Update docker logs for an action using Kafka (with REST fallback).

        Args:
            action_record_id: ID of the action record
            log_content: Content of the logs to update

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Updating docker logs for action %s", action_record_id)

        payload = {
            "actionRecordId": action_record_id,
            "logContent": log_content,
        }

        def rest_fallback():
            path = "/v1/actions/update_action_docker_logs"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Docker logs updated successfully",
                "Could not update the docker logs",
            )

        return self._hybrid_request(
            api="update_action_docker_logs",
            payload=payload,
            request_topic=self.kafka_config["action_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["action_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )
    
    def update_action_container_id(self, action_record_id, container_id):
        """Update container ID for an action using Kafka (with REST fallback).

        Args:
            action_record_id: ID of the action record
            container_id: Container ID to update

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Updating container ID for action %s", action_record_id)

        payload = {
            "actionRecordId": action_record_id,
            "containerId": container_id,
        }

        path = "/v1/actions/update_action_container_id"
        resp = self.rpc.put(path=path, payload=payload)
        return self.handle_response(
                resp,
                "Container ID updated successfully",
                "Could not update the container ID",
        )

    @log_errors(log_error=True)
    def get_docker_hub_credentials(self):
        """Get Docker Hub credentials using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Getting docker credentials")

        payload = {}

        def rest_fallback():
            path = "/v1/compute/get_docker_hub_credentials"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Docker credentials fetched successfully",
                "Could not fetch the docker credentials",
            )

        return self._hybrid_request(
            api="get_docker_hub_credentials",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def get_open_ports_config(self):
        """Get open ports configuration using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        payload = {"instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/compute/get_open_ports/{self.instance_id}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Open ports config fetched successfully",
                "Could not fetch the open ports config",
            )

        return self._hybrid_request(
            api="get_open_ports_config",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(default_return=None, log_error=True)
    def get_open_port(self):
        """Get an available open port.

        Returns:
            Port number if available, None otherwise
        """
        port_range = {"from": 8200, "to": 9000}
        try:
            resp, err, msg = self.get_open_ports_config()
            if not err and resp and resp[0]:
                port_range = resp[0]
            else:
                logging.warning("Using default port range 8200-9000 due to config fetch error")
        except Exception as err:
            logging.warning(
                "Using default port range 8200-9000. Config fetch failed: %s",
                str(err),
            )
        min_port = port_range["from"]
        max_port = port_range["to"]
        for port in range(min_port, max_port):
            if port in self.used_ports:
                continue
            self.used_ports.add(port)
            ports_value = ",".join(str(p) for p in self.used_ports)
            os.environ["USED_PORTS"] = str(ports_value)
            logging.info("Found available port: %s", port)
            return port
        logging.error(
            "No available ports found in range %s-%s",
            min_port,
            max_port,
        )
        return None

    @log_errors(default_return="", log_error=False)
    def get_data_processing_image(self):
        """Get data processing image name.

        Returns:
            Full image name including repository and tag
        """
        logging.info("Getting data processing image")
        return f"285699223019.dkr.ecr.us-west-2.amazonaws.com/{os.environ.get('ENV', 'prod')}-data-processing:latest"

    @log_errors(log_error=True)
    def get_model_secret_keys(self, secret_name):
        """Get model secret keys using Kafka (with REST fallback).

        Args:
            secret_name: Name of the secret

        Returns:
            Tuple of (data, error, message) from API response
        """
        payload = {"secret_name": secret_name}

        def rest_fallback():
            path = f"/v1/compute/get_models_secret_keys?secret_name={secret_name}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Secret keys fetched successfully",
                "Could not fetch the secret keys",
            )

        return self._hybrid_request(
            api="get_model_secret_keys",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def get_model_codebase(self, model_family_id):
        """Get model codebase.

        Args:
            model_family_id: ID of the model family

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/model_store/get_user_code_download_path/{model_family_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Codebase fetched successfully",
            "Could not fetch the codebase",
        )

    @log_errors(log_error=True)
    def get_model_codebase_requirements(self, dockerId):
        """Get model codebase requirements.

        Args:
            dockerId: ID of the docker

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/model_store/get_user_requirements_download_path/{dockerId}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Codebase requirements fetched successfully",
            "Could not fetch the codebase requirements",
        )

    @log_errors(log_error=True)
    def get_model_codebase_script(self, model_family_id):
        """Get model codebase script.

        Args:
            model_family_id: ID of the model family

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/model_store/get_user_script_download_path/:{model_family_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Codebase script fetched successfully",
            "Could not fetch the codebase script",
        )

    @log_errors(log_error=True)
    def add_account_compute_instance(
        self,
        account_number,
        alias,
        service_provider,
        instance_type,
        shut_down_time,
        lease_type,
        launch_duration,
    ):
        """Add a compute instance for an account.

        Args:
            account_number: Account number
            alias: Instance alias
            service_provider: Cloud service provider
            instance_type: Type of instance
            shut_down_time: Time to shutdown
            lease_type: Type of lease
            launch_duration: Duration to launch

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = "/v1/scaling/add_account_compute_instance"
        payload = {
            "accountNumber": account_number,
            "alias": alias,
            "serviceProvider": service_provider,
            "instanceType": instance_type,
            "shutDownTime": shut_down_time,
            "leaseType": lease_type,
            "launchDuration": launch_duration,
        }
        resp = self.rpc.post(path=path, payload=payload)
        return self.handle_response(
            resp,
            "Compute instance added successfully",
            "Could not add the compute instance",
        )

    @log_errors(log_error=True)
    def stop_account_compute(self, account_number, alias):
        """Stop a compute instance for an account using Kafka (with REST fallback).

        Args:
            account_number: Account number
            alias: Instance alias

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Stopping account compute for %s/%s", account_number, alias)

        payload = {
            "account_number": account_number,
            "alias": alias,
        }

        def rest_fallback():
            path = f"/v1/compute/stop_account_compute/{account_number}/{alias}"
            resp = self.rpc.put(path=path)
            return self.handle_response(
                resp,
                "Compute instance stopped successfully",
                "Could not stop the compute instance",
            )

        return self._hybrid_request(
            api="stop_account_compute",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def restart_account_compute(self, account_number, alias):
        """Restart a compute instance for an account using Kafka (with REST fallback).

        Args:
            account_number: Account number
            alias: Instance alias

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Restarting account compute for %s/%s", account_number, alias)

        payload = {
            "account_number": account_number,
            "alias": alias,
        }

        def rest_fallback():
            path = f"/v1/compute/restart_account_compute/{account_number}/{alias}"
            resp = self.rpc.put(path=path)
            return self.handle_response(
                resp,
                "Compute instance restarted successfully",
                "Could not restart the compute instance",
            )

        return self._hybrid_request(
            api="restart_account_compute",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def delete_account_compute(self, account_number, alias):
        """Delete a compute instance for an account.

        Args:
            account_number: Account number
            alias: Instance alias

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/scaling/delete_account_compute/{account_number}/{alias}"
        resp = self.rpc.delete(path=path)
        return self.handle_response(
            resp,
            "Compute instance deleted successfully",
            "Could not delete the compute instance",
        )

    @log_errors(log_error=True)
    def get_all_instances_type(self):
        """Get all instance types using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        payload = {}

        def rest_fallback():
            path = "/v1/compute/get_all_instances_type"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "All instance types fetched successfully",
                "Could not fetch the instance types",
            )

        return self._hybrid_request(
            api="get_all_instances_type",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )

    @log_errors(log_error=True)
    def get_compute_details(self):
        """Get compute instance details using Kafka (with REST fallback).

        Returns:
            Tuple of (data, error, message) from API response
        """
        payload = {"instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/compute/get_compute_details/{self.instance_id}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Compute details fetched successfully",
                "Could not fetch the compute details",
            )

        return self._hybrid_request(
            api="get_compute_details",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )
    
    @log_errors(log_error=True)
    def get_user_access_key_pair(self, user_id):
        """Get user access key pair using Kafka (with REST fallback).

        Args:
            user_id: ID of the user

        Returns:
            Tuple of (data, error, message) from API response
        """
        payload = {"user_id": user_id, "instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/compute/get_user_access_key_pair/{user_id}/{self.instance_id}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "User access key pair fetched successfully",
                "Could not fetch the user access key pair",
            )

        return self._hybrid_request(
            api="get_user_access_key_pair",
            payload=payload,
            request_topic=self.kafka_config["compute_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["compute_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )
    

    
    def report_architecture_info(self):
        """Collects and sends architecture info to the compute service."""
        cpu_arch = platform.machine()
        cpu_name = None
        total_memory_gb = None
        gpu_provider = None
        gpu_arch = None
        cuda_version = None
        is_jetson = False
        gpu_arch_family = None
        gpu_compute_cap = None

        if cpu_arch== "x86_64":
            cpu_arch = "x86"
        elif cpu_arch == "aarch64":
            cpu_arch = "arm64"

        # Get CPU name
        try:
            cpu_info = subprocess.run(["lscpu"], capture_output=True, text=True)
            if cpu_info.returncode == 0:
                for line in cpu_info.stdout.splitlines():
                    if "Model name:" in line:
                        cpu_name = line.split("Model name:")[-1].strip()
                        break
            # Fallback for systems without lscpu
            if not cpu_name:
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if "model name" in line:
                                cpu_name = line.split(":")[-1].strip()
                                break
                except Exception:
                    pass
        except Exception:
            pass

        # Get total memory in GB
        try:
            total_memory_bytes = psutil.virtual_memory().total
            total_memory_gb = round(total_memory_bytes / (1024 ** 3), 2)
        except Exception:
            try:
                # Fallback using /proc/meminfo
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if "MemTotal:" in line:
                            mem_kb = int(line.split()[1])
                            total_memory_gb = round(mem_kb / (1024 ** 2), 2)
                            break
            except Exception:
                pass

        # Jetson detection first (avoid nvidia-smi on Jetson)
        try:
            with open("/proc/device-tree/model") as f:
                model = f.read().lower()
                if "jetson" in model or "tegra" in model:
                    is_jetson = True
                    gpu_provider = "NVIDIA"
                    
                    # Detect specific Jetson model for GPU architecture
                    if "orin" in model:
                        if "agx" in model:
                            gpu_arch_family = "Jetson Orin AGX"
                        elif "nx" in model:
                            gpu_arch_family = "Jetson Orin NX"
                        elif "nano" in model:
                            gpu_arch_family = "Jetson Orin Nano"
                        else:
                            gpu_arch_family = "Jetson Orin"
                    elif "thor" in model:
                        gpu_arch_family = "Jetson Thor"
                    elif "xavier" in model:
                        if "agx" in model:
                            gpu_arch_family = "Jetson Xavier AGX"
                        elif "nx" in model:
                            gpu_arch_family = "Jetson Xavier NX"
                        else:
                            gpu_arch_family = "Jetson Xavier"
                    elif "nano" in model and "orin" not in model:
                        gpu_arch_family = "Jetson Nano"
                    elif "tx2" in model:
                        gpu_arch_family = "Jetson TX2"
                    elif "tx1" in model:
                        gpu_arch_family = "Jetson TX1"
                    else:
                        gpu_arch_family = "Jetson (Unknown Model)"
                    
                    # Set gpu_arch to the full model string for detailed info
                    gpu_arch = model.strip()
                    
                    try:
                        cuda_result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
                        if cuda_result.returncode == 0:
                            for line in cuda_result.stdout.splitlines():
                                if "release" in line:
                                    cuda_version = line.split("release")[-1].split(",")[0].strip()
                                    break
                    except Exception:
                        pass
                    # Fallback to nvidia-smi for CUDA version if nvcc failed
                    if not cuda_version:
                        try:
                            nvidia_smi_result = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], capture_output=True, text=True)
                            if nvidia_smi_result.returncode == 0:
                                # nvidia-smi doesn't directly give CUDA version, but we can infer it's available
                                cuda_version = "Available (via nvidia-smi)"
                        except Exception:
                            pass
        except Exception:
            pass

        # If not Jetson, try NVIDIA (nvidia-smi)
        if not is_jetson:
            try:
                result = subprocess.run(["nvidia-smi", "--query-gpu=name,compute_cap", "--format=csv,noheader"], capture_output=True, text=True)
                if result.returncode == 0:
                    gpu_provider = "NVIDIA"
                    gpu_info = result.stdout.strip().split("\n")[0].split(",")
                    gpu_arch = gpu_info[0].strip() if len(gpu_info) > 0 else None
                    gpu_compute_cap = gpu_info[1].strip() if len(gpu_info) > 1 else None
                    # Map compute capability to arch family
                    if gpu_compute_cap:
                        major = int(gpu_compute_cap.split(".")[0])
                        if major == 5:
                            gpu_arch_family = "Maxwell"
                        elif major == 6:
                            gpu_arch_family = "Pascal"
                        elif major == 7:
                            gpu_arch_family = "Volta"
                        elif major == 8:
                            gpu_arch_family = "Ampere"
                        elif major == 9:
                            gpu_arch_family = "Hopper"
                        elif major == 10:
                            gpu_arch_family = "Blackwell"
                        else:
                            gpu_arch_family = "Unknown"
                    # Get CUDA version
                    cuda_result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
                    if cuda_result.returncode == 0:
                        for line in cuda_result.stdout.splitlines():
                            if "release" in line:
                                cuda_version = line.split("release")[-1].split(",")[0].strip()
                                break
            except FileNotFoundError:
                pass

        # Try AMD if NVIDIA not found
        if gpu_provider is None:
            try:
                result = subprocess.run(["lspci"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if "AMD" in line or "Advanced Micro Devices" in line:
                            gpu_provider = "AMD"
                            gpu_arch = line.strip()
                            break
            except FileNotFoundError:
                pass

        # Only send if provider is NVIDIA or AMD
        if gpu_provider in ("NVIDIA", "AMD"):
            payload = {
                "instance_id": self.instance_id,
                "cpu_architecture": cpu_arch,
                "cpu_name": cpu_name if cpu_name else "Unknown",
                "total_memory_gb": total_memory_gb if total_memory_gb else 0,
                "gpu_provider": gpu_provider,
                "gpu_architecture": gpu_arch_family if gpu_arch_family else "Unknown",
                "gpu": gpu_arch,
                "cuda_version": cuda_version if cuda_version else "N/A",
                "is_jetson": is_jetson
            }
        else:
            payload = {
            "instance_id": self.instance_id,
            "cpu_architecture": cpu_arch,
            "cpu_name": cpu_name if cpu_name else "Unknown",
            "total_memory_gb": total_memory_gb if total_memory_gb else 0,
            "gpu_provider": "None",
            "gpu_architecture": "None",
            "gpu": "None",
            "cuda_version": "N/A",
            "is_jetson": False
        }
        
        #report for a simple cpu only instance
        
        path = "/v1/compute/report_architecture_info"
        resp = self.rpc.post(path=path, payload=payload)
        return self.handle_response(
            resp,
            "Architecture info reported successfully",
            "Could not report architecture info",
        )
    


    @log_errors(log_error=True)
    def get_internal_api_key(self, action_id):
        """Get internal API key using Kafka (with REST fallback).

        Args:
            action_id: ID of the action

        Returns:
            Tuple of (data, error, message) from API response
        """
        payload = {"action_id": action_id, "instance_id": self.instance_id}

        def rest_fallback():
            path = f"/v1/actions/get_internal_api_key/{action_id}/{self.instance_id}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "internal keys fetched successfully",
                "Could not fetch internal keys",
            )

        return self._hybrid_request(
            api="get_internal_api_key",
            payload=payload,
            request_topic=self.kafka_config["action_request_topic"] if self.enable_kafka else None,
            response_topic=self.kafka_config["action_response_topic"] if self.enable_kafka else None,
            rest_fallback_func=rest_fallback
        )
