"""Module providing __init__ functionality."""

import subprocess
import logging

from matrice_common.utils import dependencies_check

dependencies_check(
    ["docker", "psutil", "cryptography", "notebook", "aiohttp", "kafka-python"]
)

subprocess.run( # Re-upgrade docker to avoid missing DOCKER_HOST connection error
    ["pip", "install", "--upgrade", "docker"],
    check=True,
    stdout=subprocess.DEVNULL,   # suppress normal output
    stderr=subprocess.DEVNULL    # suppress warnings/progress
)

from matrice_compute.instance_manager import InstanceManager  # noqa: E402

logging.getLogger("kafka").setLevel(logging.INFO)
logging.getLogger("confluent_kafka").setLevel(logging.INFO)

__all__ = ["InstanceManager"]
