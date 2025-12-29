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

"""Manual sanity check for connection reconnection handling.

Stops the local RabbitMQ docker container mid-connection and verifies
that the connection manager transitions through RECONNECTING back to
CONNECTED once the container is started again.
"""

from __future__ import annotations

import asyncio
from asyncio.subprocess import PIPE

from rabbitmq_mcp_connection.connection.manager import ConnectionManager
from rabbitmq_mcp_connection.schemas.connection import ConnectionConfig, ConnectionState


async def run_cmd(*args: str) -> int:
    """Run a command and echo its stdout/stderr to the console."""

    proc = await asyncio.create_subprocess_exec(*args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await proc.communicate()
    if stdout:
        print(stdout.decode().strip())
    if stderr:
        print(stderr.decode().strip())
    return proc.returncode or 0


async def wait_for_state(
    manager: ConnectionManager, desired: ConnectionState, timeout: float
) -> None:
    """Poll the manager state until it matches *desired* or timeout expires."""

    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if manager.state == desired:
            return
        await asyncio.sleep(0.5)
    raise RuntimeError(
        f"Timed out waiting for state {desired.value}, current: {manager.state.value}"
    )


async def main() -> None:
    manager = ConnectionManager(ConnectionConfig())
    container_started = False

    await manager.connect()
    method = (
        "add_close_callback"
        if manager.monitor and manager.monitor._callback_collection is None
        else "close_callbacks"
    )
    print(f"monitor method: {method}")

    try:
        await asyncio.sleep(1.0)
        print("Stopping RabbitMQ container...")
        stop_rc = await run_cmd("docker", "stop", "rabbitmq")
        print(f"docker stop rc: {stop_rc}")

        try:
            await wait_for_state(manager, ConnectionState.RECONNECTING, timeout=10.0)
            print(f"manager state after stop: {manager.state.value}")
        except RuntimeError as exc:
            print(f"WARNING: {exc}")

        await asyncio.sleep(5.0)
        print("Starting RabbitMQ container...")
        start_rc = await run_cmd("docker", "start", "rabbitmq")
        print(f"docker start rc: {start_rc}")
        container_started = start_rc == 0

        try:
            await wait_for_state(manager, ConnectionState.CONNECTED, timeout=90.0)
            print(f"manager state after restart: {manager.state.value}")
        except RuntimeError as exc:
            print(f"ERROR: {exc}")
    finally:
        if not container_started:
            print("Ensuring container is running...")
            await run_cmd("docker", "start", "rabbitmq")
        await manager.disconnect()
        print(f"manager final state: {manager.state.value}")


if __name__ == "__main__":
    asyncio.run(main())
