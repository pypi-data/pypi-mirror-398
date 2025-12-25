"""
Compute Operations Handler - Kafka Event-Driven Operations Manager

This module handles compute instance operations (start/stop/restart) triggered from
the frontend dashboard via Kafka events. It consumes events from the 'compute_operations'
topic and performs the actual operations on compute instances and their actions.

Uses EventListener from matrice_common for simplified Kafka consumption.

Event Structure:
{
    "instance_id": "string",
    "action_record_id": "string",  # Can be ObjectID("000000000000000000000000") or all zeros for instance-level operations
    "operation": "start|stop|restart",
    "account_number": 12345,
    "requested_by": "user@example.com",
    "request_id": "uuid-string",
    "timestamp": "2025-11-21T10:30:00.123Z"
}
"""

import logging
import re
import time
from typing import Dict, Any, Optional
import sys
import traceback
import os
import subprocess

from matrice_common.stream.event_listener import EventListener

# Configure logging
logger = logging.getLogger(__name__)


class ComputeOperationsHandler:
    """
    Handles Kafka-based compute operations for instance and action management.

    This class uses EventListener from matrice_common to listen for operation
    events from the 'compute_operations' Kafka topic. It delegates operations
    to the ActionsManager for execution and updates status via API calls.
    """

    KAFKA_TOPIC = "compute_operations"

    def __init__(self, actions_manager, session, scaling, instance_id: str):
        """
        Initialize the Compute Operations Handler.

        Args:
            actions_manager: Reference to the ActionsManager instance
            session: Session object for authentication and Kafka configuration
            scaling: Scaling service instance for API status updates
            instance_id: This compute instance's ID for filtering events
        """
        self.actions_manager = actions_manager
        self.session = session
        self.scaling = scaling
        self.instance_id = instance_id
        self.event_listener: Optional[EventListener] = None
        self.running = False

        logger.info(f"Initializing ComputeOperationsHandler for instance ID: {instance_id}")

    def start(self) -> bool:
        """
        Start the operations handler using EventListener.

        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("ComputeOperationsHandler is already running")
            return False

        try:
            self.event_listener = EventListener(
                session=self.session,
                topics=[self.KAFKA_TOPIC],
                event_handler=self._handle_operation_event,
                filter_field='instance_id',
                filter_value=self.instance_id,
                consumer_group_id=f"compute_ops_{self.instance_id}"
            )
            self.running = self.event_listener.start()

            if self.running:
                logger.info("ComputeOperationsHandler started successfully")
            else:
                logger.error("ComputeOperationsHandler failed to start")

            return self.running

        except Exception as e:
            logger.error(f"Failed to start ComputeOperationsHandler: {e}")
            logger.error(traceback.format_exc())
            return False

    def stop(self):
        """
        Stop the operations handler gracefully.
        """
        logger.info("Stopping ComputeOperationsHandler...")
        self.running = False

        if self.event_listener:
            self.event_listener.stop()

        logger.info("ComputeOperationsHandler stopped")

    def _handle_operation_event(self, event: Dict[str, Any]):
        """
        Handle incoming operation event from Kafka.

        This is the callback function passed to EventListener.

        Args:
            event: The operation event dictionary
        """
        logger.info(f"Received operation event: {event}")

        # Validate event structure
        if not self._validate_event(event):
            logger.error(f"Invalid event structure: {event}")
            return

        # Process the operation
        self._process_operation(event)

    def _is_instance_level_operation(self, action_record_id: str) -> bool:
        """
        Check if action_record_id represents an instance-level operation.
        Instance-level operations are identified by action_record_id containing only zeros,
        which can come in various formats:
        - "000000000000000000000000"
        - "ObjectID(\"000000000000000000000000\")"
        - "ObjectID('000000000000000000000000')"

        Args:
            action_record_id: The action record ID to check

        Returns:
            True if this is an instance-level operation, False otherwise
        """
        if not action_record_id:
            return False

        # Handle ObjectID("...") or ObjectID('...') format from Kafka messages
        clean_id = action_record_id
        if 'ObjectID' in action_record_id:
            match = re.search(r'ObjectID\(["\']([^"\']+)["\']\)', action_record_id)
            if match:
                clean_id = match.group(1)

        # Check if the string contains only zeros (any length)
        return clean_id.replace('0', '') == ''

    def _extract_action_record_id(self, action_record_id: str) -> str:
        """
        Extract the actual action record ID from various formats.

        Args:
            action_record_id: The raw action record ID (may be wrapped in ObjectID)

        Returns:
            The extracted action record ID string
        """
        if not action_record_id:
            return action_record_id

        # Handle ObjectID("...") or ObjectID('...') format
        if 'ObjectID' in action_record_id:
            match = re.search(r'ObjectID\(["\']([^"\']+)["\']\)', action_record_id)
            if match:
                return match.group(1)

        return action_record_id

    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """
        Validate that the event has all required fields.

        Args:
            event: The event dictionary to validate

        Returns:
            True if event is valid, False otherwise
        """
        required_fields = [
            "instance_id",
            "action_record_id",
            "operation",
            "account_number",
            "requested_by",
            "request_id",
            "timestamp"
        ]

        for field in required_fields:
            if field not in event:
                logger.error(f"Missing required field: {field}")
                return False

        # Validate operation type
        valid_operations = ["start", "stop", "restart"]
        if event["operation"] not in valid_operations:
            logger.error(f"Invalid operation: {event['operation']}. Must be one of {valid_operations}")
            return False

        return True

    def _process_operation(self, event: Dict[str, Any]):
        """
        Process a compute operation event.

        Args:
            event: The operation event dictionary
        """
        operation = event["operation"]
        raw_action_record_id = event["action_record_id"]
        action_record_id = self._extract_action_record_id(raw_action_record_id)
        request_id = event["request_id"]
        requested_by = event["requested_by"]

        logger.info(f"Processing {operation} operation for action {action_record_id} "
                   f"(request: {request_id}, user: {requested_by})")

        try:
            # Check if this is an instance-level operation (action_record_id contains only zeros)
            is_instance_operation = self._is_instance_level_operation(raw_action_record_id)

            if is_instance_operation:
                result = self._handle_instance_operation(operation, event)
            else:
                result = self._handle_action_operation(operation, action_record_id, event)

            # Update status via API and logging
            self._update_operation_status(event, action_record_id, "completed", result)

        except Exception as e:
            error_msg = f"Operation failed: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            # Update failure status
            self._update_operation_status(event, action_record_id, "failed", {"error": error_msg})

    def _handle_action_operation(self, operation: str, action_record_id: str,
                                 event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle operations on a specific action.

        Args:
            operation: The operation type (start/stop/restart)
            action_record_id: The action record ID to operate on
            event: The full event dictionary

        Returns:
            Result dictionary with operation details
        """
        if operation == "start":
            return self._start_action(action_record_id, event)
        elif operation == "stop":
            return self._stop_action(action_record_id, event)
        elif operation == "restart":
            return self._restart_action(action_record_id, event)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def _handle_instance_operation(self, operation: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle operations on the entire instance (the Python application itself).

        Args:
            operation: The operation type (start/stop/restart)
            event: The full event dictionary

        Returns:
            Result dictionary with operation details (may not return if app is killed/restarted)
        """
        logger.info(f"Executing instance-level {operation} operation on Python application")

        if operation == "stop":
            # Kill the Python application itself
            logger.critical("Instance-level STOP: Killing Python application process")
            try:
                # Log status before killing
                logger.warning(
                    f"Operation {operation} on instance {self.instance_id}: "
                    f"completed - killing_application (PID: {os.getpid()})"
                )
                # Give a moment for logs to be written
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to log status before kill: {e}")

            # Forcefully exit the application
            logger.critical(f"Terminating Python application (PID: {os.getpid()})")
            os._exit(0)  # Forceful exit, doesn't call cleanup handlers

        elif operation == "restart":
            # Restart the Python application itself
            logger.critical("Instance-level RESTART: Restarting Python application process")
            try:
                # Log status before restarting
                logger.warning(
                    f"Operation {operation} on instance {self.instance_id}: "
                    f"completed - restarting_application (PID: {os.getpid()})"
                )
                # Give a moment for logs to be written
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to log status before restart: {e}")

            # Restart the application
            logger.critical(f"Restarting Python application (PID: {os.getpid()})")
            self._restart_application()

        elif operation == "start":
            # Start doesn't make sense for instance-level
            logger.warning("Start operation not supported at instance level")
            return {
                "operation": operation,
                "instance_level": True,
                "status": "not_supported",
                "message": "Start operation is not supported at instance level"
            }

        # This should not be reached for stop/restart operations
        return {
            "operation": operation,
            "instance_level": True,
            "status": "completed"
        }

    def _restart_application(self):
        """
        Restart the Python application by replacing the current process.
        This uses os.execv() to replace the current process with a new one.
        """
        try:
            python_executable = sys.executable
            script_args = sys.argv

            logger.info(f"Restarting with: {python_executable} {' '.join(script_args)}")

            # Use os.execv() to replace the current process
            # This will restart the application with the same arguments
            os.execv(python_executable, [python_executable] + script_args)

        except Exception as e:
            logger.error(f"Failed to restart application: {e}")
            logger.error(traceback.format_exc())
            # Fallback: try using subprocess to start a new process and exit
            try:
                logger.info("Attempting fallback restart method")
                python_executable = sys.executable
                script_args = sys.argv

                # Start new process
                subprocess.Popen([python_executable] + script_args)
                # Exit current process
                logger.critical("New process started, exiting current process")
                os._exit(0)
            except Exception as fallback_error:
                logger.error(f"Fallback restart also failed: {fallback_error}")
                logger.error(traceback.format_exc())
                # Last resort: just exit
                os._exit(1)

    def _start_action(self, action_record_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a specific action.

        Args:
            action_record_id: The action record ID to start
            event: The full event dictionary

        Returns:
            Result dictionary
        """
        logger.info(f"Starting action: {action_record_id}")

        # Check if action is already running
        current_actions = self.actions_manager.get_current_actions()
        if action_record_id in current_actions:
            action_instance = current_actions[action_record_id]
            if action_instance.is_running():
                logger.warning(f"Action {action_record_id} is already running")
                return {
                    "status": "already_running",
                    "action_id": action_record_id
                }

        # Fetch action details from backend and start it
        # This will be handled by the ActionsManager's normal flow
        # Force a fetch to pick up this specific action
        self.actions_manager.fetch_actions()

        return {
            "status": "started",
            "action_id": action_record_id
        }

    def _stop_action(self, action_record_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stop a specific action.

        Args:
            action_record_id: The action record ID to stop
            event: The full event dictionary

        Returns:
            Result dictionary
        """
        logger.info(f"Stopping action: {action_record_id}")

        result = self.actions_manager.stop_action(action_record_id)

        return {
            "status": "stopped",
            "action_id": action_record_id,
            "details": result
        }

    def _restart_action(self, action_record_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restart a specific action.

        Args:
            action_record_id: The action record ID to restart
            event: The full event dictionary

        Returns:
            Result dictionary
        """
        logger.info(f"Restarting action: {action_record_id}")

        result = self.actions_manager.restart_action(action_record_id)

        return {
            "status": "restarted",
            "action_id": action_record_id,
            "details": result
        }

    def _update_operation_status(self, event: Dict[str, Any], action_record_id: str,
                                 status: str, result: Dict[str, Any]):
        """
        Update operation status via API and logging.

        Args:
            event: The original event
            action_record_id: The extracted action record ID
            status: Operation status (completed/failed)
            result: Result details
        """
        operation = event["operation"]
        request_id = event["request_id"]

        # Log status as warning for visibility
        logger.warning(
            f"Operation {operation} on {action_record_id}: {status} - "
            f"request_id={request_id}, result={result}"
        )

        # Update via API (for action-level operations only)
        if not self._is_instance_level_operation(event["action_record_id"]):
            try:
                # Determine isRunning based on operation and status
                is_running = False
                if status == "completed":
                    if operation == "start":
                        is_running = True
                    elif operation == "restart":
                        is_running = True
                    elif operation == "stop":
                        is_running = False

                self.scaling.update_action_status(
                    service_provider=os.environ.get("SERVICE_PROVIDER", ""),
                    action_record_id=action_record_id,
                    status=status,
                    isRunning=is_running,
                )
                logger.info(f"API status updated for action {action_record_id}: {status}")
            except Exception as e:
                logger.error(f"Failed to update API status for action {action_record_id}: {e}")
