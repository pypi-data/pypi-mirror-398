"""Module providing actions_manager functionality."""

import logging
import os
import time
from matrice_compute.action_instance import (
    ActionInstance,
)
from matrice_compute.instance_utils import (
    has_gpu,
    get_mem_usage,
    cleanup_docker_storage,
)
from matrice_compute.scaling import (
    Scaling,
)
from matrice_common.utils import log_errors


class ActionsManager:
    """Class for managing actions."""

    def __init__(self, scaling: Scaling):
        """Initialize an action manager.

        Args:
            scaling (Scaling): Scaling service instance
        """
        self.current_actions: dict[str, ActionInstance] = {}
        self.stopped_actions: dict[str, ActionInstance] = {}  # Track stopped actions separately
        self.scaling = scaling
        self.memory_threshold = 0.9
        self.poll_interval = 10
        self.last_actions_check = 0
        logging.info("ActionsManager initialized")

    @log_errors(default_return=[], raise_exception=False)
    def fetch_actions(self) -> list:
        """Poll for actions and process them if memory threshold is not exceeded.

        Returns:
            list: List of fetched actions
        """
        actions = []
        logging.info("Polling backend for new jobs")
        result = self.scaling.assign_jobs(has_gpu())
        if result is None:
            logging.error("assign_jobs returned None")
            return actions
        fetched_actions, error, _ = result
        if error:
            logging.error("Error assigning jobs: %s", error)
            return actions
        if not isinstance(fetched_actions, list):
            fetched_actions = [fetched_actions]
        for action in fetched_actions:
            if not action:
                continue
            if action["_id"] != "000000000000000000000000":
                actions.append(action)
                logging.info(
                    "Fetched action details: %s",
                    actions,
                )
        return actions

    @log_errors(default_return=None, raise_exception=False)
    def process_action(self, action: dict) -> ActionInstance:
        """Process the given action.

        Args:
            action (dict): Action details to process

        Returns:
            ActionInstance: Processed action instance or None if failed
        """
        logging.info(
            "Processing action: %s",
            action["_id"],
        )
        action_instance = ActionInstance(self.scaling, action)
        self.scaling.update_action_status(
            service_provider=os.environ["SERVICE_PROVIDER"],
            action_record_id=action["_id"],
            status="starting",
            action_duration=0,
        )
        logging.info("locking action")
        self.scaling.update_action_status(
            service_provider=os.environ["SERVICE_PROVIDER"],
            status="started",
            action_record_id=action["_id"],
            isRunning=True,
            action_duration=0,
            cpuUtilisation=0.0,
            gpuUtilisation=0.0,
            memoryUtilisation=0.0,
            gpuMemoryUsed=0,
        )
        self.scaling.update_status(
            action["_id"],
            action["action"],
            "bg-job-scheduler",
            "JBSS_LCK",
            "OK",
            "Job is locked for processing",
        )
        action_instance.execute()
        logging.info(
            "action %s started.",
            action_instance.action_record_id,
        )
        return action_instance

    @log_errors(raise_exception=False)
    def process_actions(self) -> None:
        """Process fetched actions."""
        for action in self.fetch_actions():
            action_id = action["_id"]
            
            # Skip if action is already running in current_actions
            if action_id in self.current_actions:
                logging.info("Action %s already in current_actions, skipping", action_id)
                continue
            
            # If action exists in stopped_actions, remove it before starting fresh
            if action_id in self.stopped_actions:
                logging.info("Action %s found in stopped_actions, removing before restart", action_id)
                del self.stopped_actions[action_id]
            
            # Process and add to current_actions
            action_instance = self.process_action(action)
            if action_instance:
                # Ensure action is not in stopped_actions (defensive check)
                if action_id in self.stopped_actions:
                    del self.stopped_actions[action_id]
                self.current_actions[action_id] = action_instance

    @log_errors(raise_exception=False)
    def update_actions_status(self) -> None:
        """Update tracking of running vs stopped actions.

        This method checks all actions and moves stopped ones to stopped_actions dict
        without deleting them. This prevents interference with compute operations
        handler while maintaining accurate status reporting.
        """
        moved_to_stopped = 0

        # Check each action and update its status
        for action_id, instance in list(self.current_actions.items()):
            is_running = False
            status_reason = ""

            # Check if process is running
            if hasattr(instance, 'is_running'):
                try:
                    is_running = instance.is_running()
                except Exception as e:
                    logging.error("Error checking is_running for action %s: %s", action_id, str(e))
                    is_running = False
                    status_reason = f"error checking status: {str(e)}"

            # Check for process object validity
            if not is_running and not status_reason:
                if not hasattr(instance, 'process') or instance.process is None:
                    status_reason = "no process object"
                else:
                    status_reason = "process not running"

            # Move to stopped_actions if not running (but don't delete)
            if not is_running:
                logging.info(
                    "Action %s moved to stopped_actions: %s",
                    action_id,
                    status_reason
                )
                # Ensure action is removed from current_actions before adding to stopped_actions
                if action_id in self.current_actions:
                    del self.current_actions[action_id]
                # Ensure action is not duplicated in stopped_actions
                if action_id not in self.stopped_actions:
                    self.stopped_actions[action_id] = instance
                moved_to_stopped += 1

        # Log current state
        running_ids = list(self.current_actions.keys())
        stopped_ids = list(self.stopped_actions.keys())

        if self.current_actions or self.stopped_actions:
            logging.info(
                "Actions status: %d running %s, %d stopped %s",
                len(self.current_actions),
                running_ids if running_ids else "[]",
                len(self.stopped_actions),
                stopped_ids if stopped_ids else "[]"
            )

    @log_errors(raise_exception=False)
    def purge_unwanted(self) -> None:
        """Purge completed or failed actions.

        NOTE: This now calls update_actions_status() which moves stopped actions
        to a separate dict instead of deleting them. This prevents interference
        with compute operations handler while maintaining accurate status.
        """
        self.update_actions_status()

    @log_errors(default_return={}, raise_exception=False)
    def get_current_actions(self) -> dict:
        """Get the current running actions.

        This method:
        1. Updates action status tracking via update_actions_status()
        2. Returns only the running actions (current_actions dict)
        3. Provides detailed logging about current actions state

        Returns:
            dict: Current running actions only
        """
        # Update status tracking (moves stopped to stopped_actions)
        self.update_actions_status()

        if self.current_actions:
            action_ids = list(self.current_actions.keys())
            logging.info(
                "Currently running %d actions: %s",
                len(self.current_actions),
                action_ids
            )
        else:
            logging.info("No actions currently running")

        return self.current_actions

    @log_errors(default_return={}, raise_exception=False)
    def get_all_actions(self) -> dict:
        """Get all tracked actions (both running and stopped).

        Returns:
            dict: All tracked actions with their status
        """
        all_actions = {}
        for action_id, instance in self.current_actions.items():
            all_actions[action_id] = {"instance": instance, "status": "running"}
        for action_id, instance in self.stopped_actions.items():
            all_actions[action_id] = {"instance": instance, "status": "stopped"}
        return all_actions

    @log_errors(default_return={}, raise_exception=False)
    def get_stopped_actions(self) -> dict:
        """Get stopped actions.

        Returns:
            dict: Stopped actions
        """
        return self.stopped_actions

    @log_errors(default_return={}, raise_exception=False)
    def stop_action(self, action_record_id: str) -> dict:
        """Stop a specific action by its record ID.

        Args:
            action_record_id (str): The action record ID to stop

        Returns:
            dict: Result dictionary with status information
        """
        logging.info("Attempting to stop action: %s", action_record_id)

        # Check if action exists in current (running) actions
        action_instance = None
        action_source = None

        if action_record_id in self.current_actions:
            action_instance = self.current_actions[action_record_id]
            action_source = "current_actions"
        elif action_record_id in self.stopped_actions:
            # Action already in stopped_actions
            logging.info("Action %s already in stopped_actions", action_record_id)
            return {
                "success": True,
                "reason": "already_stopped",
                "action_id": action_record_id
            }
        else:
            logging.warning("Action %s not found in current or stopped actions", action_record_id)
            return {
                "success": False,
                "reason": "action_not_found",
                "action_id": action_record_id
            }

        # Check if action is actually running
        if not action_instance.is_running():
            logging.info("Action %s is not running, moving to stopped_actions", action_record_id)
            # Move to stopped_actions instead of deleting
            # Ensure action is removed from current_actions first
            if action_record_id in self.current_actions:
                del self.current_actions[action_record_id]
            # Ensure action is not duplicated in stopped_actions
            if action_record_id not in self.stopped_actions:
                self.stopped_actions[action_record_id] = action_instance
            return {
                "success": True,
                "reason": "already_stopped",
                "action_id": action_record_id
            }

        # Stop the action
        try:
            logging.info("Stopping action %s", action_record_id)
            action_instance.stop()

            # Update action status to stopped
            self.scaling.update_action_status(
                service_provider=os.environ["SERVICE_PROVIDER"],
                action_record_id=action_record_id,
                status="stopped",
                isRunning=False,
                action_duration=0,
            )

            # Move to stopped_actions instead of deleting
            # Ensure action is removed from current_actions first
            if action_record_id in self.current_actions:
                del self.current_actions[action_record_id]
            # Ensure action is not duplicated in stopped_actions
            if action_record_id not in self.stopped_actions:
                self.stopped_actions[action_record_id] = action_instance

            logging.info("Successfully stopped action: %s", action_record_id)
            return {
                "success": True,
                "action_id": action_record_id,
                "stopped_at": time.time()
            }

        except Exception as e:
            logging.error("Error stopping action %s: %s", action_record_id, str(e))
            return {
                "success": False,
                "reason": "stop_failed",
                "error": str(e),
                "action_id": action_record_id
            }

    @log_errors(default_return={}, raise_exception=False)
    def restart_action(self, action_record_id: str) -> dict:
        """Restart a specific action by its record ID.

        This method stops the action if it's running, then fetches fresh action
        details from the backend and starts it again.

        Args:
            action_record_id (str): The action record ID to restart

        Returns:
            dict: Result dictionary with status information
        """
        logging.info("Attempting to restart action: %s", action_record_id)

        # Step 1: Stop the action if it exists in current_actions or stopped_actions
        stop_result = {"success": True, "reason": "not_running"}
        if action_record_id in self.current_actions:
            logging.info("Stopping existing action %s before restart", action_record_id)
            stop_result = self.stop_action(action_record_id)

            if not stop_result.get("success"):
                logging.error("Failed to stop action %s for restart", action_record_id)
                return {
                    "success": False,
                    "reason": "stop_failed_before_restart",
                    "stop_result": stop_result,
                    "action_id": action_record_id
                }

            # Wait a moment for cleanup
            time.sleep(2)
        elif action_record_id in self.stopped_actions:
            logging.info("Action %s found in stopped_actions, will restart", action_record_id)
            stop_result = {"success": True, "reason": "was_stopped"}

        # Step 2: Fetch fresh action details from backend
        try:
            logging.info("Fetching action details for restart: %s", action_record_id)

            # Get action details via API
            action_details, error, _ = self.scaling.get_action_details(action_record_id)

            if error or not action_details:
                logging.error("Failed to fetch action details for %s: %s",
                            action_record_id, error)
                return {
                    "success": False,
                    "reason": "fetch_failed",
                    "error": error,
                    "action_id": action_record_id
                }

            # Step 3: Process (start) the action
            logging.info("Starting action %s after restart", action_record_id)
            action_instance = self.process_action(action_details)

            if action_instance:
                # Ensure action is removed from stopped_actions if present
                if action_record_id in self.stopped_actions:
                    del self.stopped_actions[action_record_id]
                # Ensure action is removed from current_actions if present (defensive check)
                if action_record_id in self.current_actions:
                    logging.warning("Action %s already in current_actions during restart, replacing", action_record_id)
                    del self.current_actions[action_record_id]
                # Add to current_actions
                self.current_actions[action_record_id] = action_instance

                logging.info("Successfully restarted action: %s", action_record_id)
                return {
                    "success": True,
                    "action_id": action_record_id,
                    "restarted_at": time.time(),
                    "stop_result": stop_result
                }
            else:
                logging.error("Failed to start action %s after restart", action_record_id)
                return {
                    "success": False,
                    "reason": "start_failed_after_restart",
                    "action_id": action_record_id
                }

        except Exception as e:
            logging.error("Error restarting action %s: %s", action_record_id, str(e))
            return {
                "success": False,
                "reason": "restart_failed",
                "error": str(e),
                "action_id": action_record_id
            }

    @log_errors(raise_exception=True)
    def start_actions_manager(self) -> None:
        """Start the actions manager main loop."""
        while True:
            waiting_time = self.poll_interval  # Default wait time
            try:
                mem_usage = get_mem_usage()
                logging.info("Memory usage: %d", mem_usage)
                waiting_time = int(
                    min(
                        self.poll_interval
                        / max(
                            0.001,
                            self.memory_threshold - mem_usage,
                        ),
                        120,
                    )
                )
                if mem_usage < self.memory_threshold:
                    self.process_actions()
                    logging.info(
                        "Waiting for %d seconds before next poll",
                        waiting_time,
                    )
                else:
                    logging.info(
                        "Memory threshold exceeded, waiting for %d seconds",
                        waiting_time,
                    )
                cleanup_docker_storage()
            except Exception as e:
                logging.error("Error in actions manager: %s", e)
            time.sleep(waiting_time)
