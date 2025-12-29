#!/usr/bin/env python3

"""
Copyright (C) 2025 Luciano Guerche

This file is part of rabbitmq-mcp-server.

rabbitmq-mcp-server is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

rabbitmq-mcp-server is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with rabbitmq-mcp-server. If not, see <https://www.gnu.org/licenses/>.
"""

"""Utility para subir um RabbitMQ local em Docker e aguardar readiness completo."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from typing import Final
from urllib.request import Request, urlopen

AMQP_PORT: Final[int] = 5672
MGMT_PORT: Final[int] = 15672
CONTAINER_NAME: Final[str] = "rabbitmq-test"
TIMEOUT_SECONDS: Final[int] = 30
CHECK_INTERVAL_SECONDS: Final[float] = 1.0


def _socket_ready(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def wait_for_rabbitmq(host: str = "localhost") -> bool:
    start_time = time.time()
    while time.time() - start_time < TIMEOUT_SECONDS:
        if _socket_ready(host, AMQP_PORT):
            try:
                req = Request(
                    f"http://{host}:{MGMT_PORT}/api/overview",
                    headers={"Authorization": "Basic dGVzdDp0ZXN0"},
                )
                with urlopen(req, timeout=2) as response:
                    data = json.loads(response.read())
                    if data.get("management_version"):
                        print(
                            f"✓ RabbitMQ ready on {host}:{AMQP_PORT} (Management: {data['management_version']})"
                        )
                        return True
            except Exception:
                pass
        time.sleep(CHECK_INTERVAL_SECONDS)
        elapsed = int(time.time() - start_time)
        print(f"  Waiting for RabbitMQ... ({elapsed}s)")
    return False


def container_running() -> bool:
    cmd = ["docker", "ps", "-q", "-f", f"name={CONTAINER_NAME}"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return bool(result.stdout.strip())


def start_rabbitmq() -> int:
    if container_running():
        print("RabbitMQ container already running")
        return 0 if wait_for_rabbitmq() else 1

    cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        CONTAINER_NAME,
        "-p",
        f"{AMQP_PORT}:{AMQP_PORT}",
        "-p",
        f"{MGMT_PORT}:{MGMT_PORT}",
        "-e",
        "RABBITMQ_DEFAULT_USER=test",
        "-e",
        "RABBITMQ_DEFAULT_PASS=test",
        "rabbitmq:3-management",
    ]
    subprocess.run(cmd, check=True)
    print("RabbitMQ container started, waiting for ready state…")
    return 0 if wait_for_rabbitmq() else 1


if __name__ == "__main__":
    sys.exit(start_rabbitmq())
