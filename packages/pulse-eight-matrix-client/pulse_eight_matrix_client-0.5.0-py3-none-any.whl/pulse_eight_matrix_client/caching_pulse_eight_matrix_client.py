"""Pulse8 HDBaseT Matrix Caching Client."""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Tuple

from .pulse_eight_matrix_client import PulseEightMatrixClient
from .models import Port, SetPortResponse

_LOGGER = logging.getLogger(__name__)


class CachingPulseEightMatrixClient(PulseEightMatrixClient):
    """Async client for Pulse8 HDBaseT Matrix with caching and auto-polling."""

    def __init__(
        self,
        host: str,
        port: int = 80,
        timeout: int = 10,
        poll_interval: int = 5,
    ):
        """
        Initialize the CachingPulse8MatrixClient.

        Args:
            host: IP address or hostname of the matrix
            port: HTTP port (default: 80)
            timeout: Request timeout in seconds (default: 10)
            poll_interval: Polling interval in seconds (default: 5)
        """
        super().__init__(host, port, timeout)
        self.poll_interval = poll_interval
        self._poll_task: Optional[asyncio.Task] = None
        self._cached_ports: List[Port] = []
        self._cached_ports_dict: Dict[Tuple[str, int], Port] = {}  # (mode, bay) -> Port
        self._last_poll_time: Optional[float] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self):
        """Create HTTP session and start polling."""
        await super().connect()
        if self._poll_task is None:
            await self.force_cache_update()
            self._poll_task = asyncio.create_task(self._poll_loop())

    async def close(self):
        """Close HTTP session and stop polling."""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        await super().close()

    async def _poll_loop(self):
        """Background polling loop to keep cached state updated."""
        try:
            while True:
                await asyncio.sleep(self.poll_interval)
                await self.force_cache_update()
                _LOGGER.debug("Updated cached state")
        except asyncio.CancelledError:
            pass
        except Exception:
            _LOGGER.exception("Error in polling loop")

    async def force_cache_update(self):
        """Update the cached ports list."""
        try:
            ports = await super().get_ports()
            self._cached_ports = ports
            self._cached_ports_dict = {(port.mode, port.bay): port for port in ports}
            self._last_poll_time = time.time()
        except Exception:
            _LOGGER.warning("Failed to update cached ports", exc_info=True)

    def get_cached_ports(self) -> List[Port]:
        """Get list of all ports from cache."""
        return self._cached_ports.copy()

    def get_cached_output_source(self, output_bay: int) -> Optional[int]:
        """Get which input is currently routed to an output from cache."""
        port = self._cached_ports_dict.get(("Output", output_bay))
        return port.receive_from if port else None

    def get_cached_input_destinations(self, input_bay: int) -> List[int]:
        """Get which outputs are receiving from an input from cache."""
        destinations = []
        for port in self._cached_ports:
            if port.mode == "Output" and port.receive_from == input_bay:
                destinations.append(port.bay)
        return destinations

    def get_cached_routing_map(self) -> Dict[int, int]:
        """Get a mapping of all output bays to their source input bays from cache."""
        routing_map = {}
        for port in self._cached_ports:
            if port.mode == "Output" and port.receive_from is not None:
                routing_map[port.bay] = port.receive_from
        return routing_map

    def get_last_poll_time(self) -> Optional[float]:
        """Get the timestamp of the last successful poll."""
        return self._last_poll_time

    def get_cache_age(self) -> Optional[float]:
        """Get the age of the cached data in seconds."""
        if self._last_poll_time is None:
            return None
        return time.time() - self._last_poll_time

    async def set_port(self, input_bay: int, output_bay: int) -> SetPortResponse:
        """
        Route an input to an output and force a cache update.
        """
        response = await super().set_port(input_bay, output_bay)
        await self.force_cache_update()
        return response

    async def route_by_name(self, input_name: str, output_name: str) -> SetPortResponse:
        """
        Route an input to an output using port names and force a cache update.
        """
        response = await super().route_by_name(input_name, output_name)
        await self.force_cache_update()
        return response
