"""
Client implementation for KXY Open ID Service
"""

import httpx
import threading
import asyncio
from typing import Optional
from .models import SegmentRequest, SegmentResponse, ApiResponse
from .exceptions import OpenIdAPIError, OpenIdConnectionError, OpenIdTimeoutError, OpenIdClientError


class SegmentClient:
    """Client for allocating ID segments from KXY Open ID Service"""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        headers: Optional[dict] = None
    ):
        """
        Initialize the SegmentClient.

        Args:
            base_url: Base URL of the KXY Open ID Service (e.g., "http://localhost:5801")
            timeout: Request timeout in seconds (default: 30.0)
            verify_ssl: Whether to verify SSL certificates (default: True)
            headers: Optional custom headers to include in all requests
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.headers = headers or {}

    def allocate_segment(
        self,
        system_code: str,
        db_name: str,
        table_name: str,
        field_name: str,
        segment_count: int = 10000
    ) -> SegmentResponse:
        """
        Allocate an ID segment.

        Args:
            system_code: System code
            db_name: Database name
            table_name: Table name
            field_name: Field name
            segment_count: Number of IDs to allocate (default: 10000)

        Returns:
            SegmentResponse: Contains start and end IDs of the allocated segment

        Raises:
            OpenIdAPIError: If the API returns an error response
            OpenIdConnectionError: If connection to the API fails
            OpenIdTimeoutError: If the request times out
        """
        request = SegmentRequest(
            system_code=system_code,
            db_name=db_name,
            table_name=table_name,
            field_name=field_name,
            segment_count=segment_count
        )

        url = f"{self.base_url}/api/segment/allocate"

        try:
            with httpx.Client(timeout=self.timeout, verify=self.verify_ssl) as client:
                response = client.post(
                    url,
                    json=request.model_dump(),
                    headers=self.headers
                )
                response.raise_for_status()

                # Parse response
                api_response = ApiResponse[SegmentResponse].model_validate(response.json())

                # Check if API returned an error
                if api_response.code != 0:
                    raise OpenIdAPIError(
                        code=api_response.code,
                        msg=api_response.msg,
                        trace_id=api_response.traceId
                    )

                return api_response.data

        except httpx.TimeoutException as e:
            raise OpenIdTimeoutError(f"Request timed out after {self.timeout}s: {str(e)}")
        except httpx.ConnectError as e:
            raise OpenIdConnectionError(f"Failed to connect to {url}: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise OpenIdConnectionError(f"HTTP error {e.response.status_code}: {str(e)}")
        except OpenIdAPIError:
            raise
        except Exception as e:
            raise OpenIdClientError(f"Unexpected error: {str(e)}")

    async def allocate_segment_async(
        self,
        system_code: str,
        db_name: str,
        table_name: str,
        field_name: str,
        segment_count: int = 10000
    ) -> SegmentResponse:
        """
        Allocate an ID segment asynchronously.

        Args:
            system_code: System code
            db_name: Database name
            table_name: Table name
            field_name: Field name
            segment_count: Number of IDs to allocate (default: 10000)

        Returns:
            SegmentResponse: Contains start and end IDs of the allocated segment

        Raises:
            OpenIdAPIError: If the API returns an error response
            OpenIdConnectionError: If connection to the API fails
            OpenIdTimeoutError: If the request times out
        """
        request = SegmentRequest(
            system_code=system_code,
            db_name=db_name,
            table_name=table_name,
            field_name=field_name,
            segment_count=segment_count
        )

        url = f"{self.base_url}/api/segment/allocate"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                response = await client.post(
                    url,
                    json=request.model_dump(),
                    headers=self.headers
                )
                response.raise_for_status()

                # Parse response
                api_response = ApiResponse[SegmentResponse].model_validate(response.json())

                # Check if API returned an error
                if api_response.code != 0:
                    raise OpenIdAPIError(
                        code=api_response.code,
                        msg=api_response.msg,
                        trace_id=api_response.traceId
                    )

                return api_response.data

        except httpx.TimeoutException as e:
            raise OpenIdTimeoutError(f"Request timed out after {self.timeout}s: {str(e)}")
        except httpx.ConnectError as e:
            raise OpenIdConnectionError(f"Failed to connect to {url}: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise OpenIdConnectionError(f"HTTP error {e.response.status_code}: {str(e)}")
        except OpenIdAPIError:
            raise
        except Exception as e:
            raise OpenIdClientError(f"Unexpected error: {str(e)}")


class IdGenerator:
    """Thread-safe ID generator using segment allocation"""

    def __init__(
        self,
        segment_client: SegmentClient,
        system_code: str,
        db_name: str,
        table_name: str,
        field_name: str,
        segment_count: int = 10000
    ):
        """
        Initialize the IdGenerator.

        Args:
            segment_client: SegmentClient instance for allocating segments
            system_code: System code
            db_name: Database name
            table_name: Table name
            field_name: Field name
            segment_count: Number of IDs to allocate per segment (default: 10000)
        """
        self.segment_client = segment_client
        self.system_code = system_code
        self.db_name = db_name
        self.table_name = table_name
        self.field_name = field_name
        self.segment_count = segment_count

        self._lock = threading.Lock()
        self._current: Optional[int] = None
        self._end: Optional[int] = None

    def _allocate_new_segment(self) -> None:
        """Allocate a new segment (must be called with lock held)"""
        segment = self.segment_client.allocate_segment(
            system_code=self.system_code,
            db_name=self.db_name,
            table_name=self.table_name,
            field_name=self.field_name,
            segment_count=self.segment_count
        )
        self._current = segment.start
        self._end = segment.end

    def next_id(self) -> int:
        """
        Generate next ID in a thread-safe manner.

        Returns:
            int: The next available ID

        Raises:
            OpenIdAPIError: If the API returns an error response
            OpenIdConnectionError: If connection to the API fails
            OpenIdTimeoutError: If the request times out
        """
        with self._lock:
            # Check if we need to allocate a segment
            if self._current is None or self._end is None:
                self._allocate_new_segment()
            # Check if current segment is exhausted
            elif self._current > self._end:
                self._allocate_new_segment()

            # Get current ID and increment
            current_id = self._current
            self._current += 1
            return current_id


class AsyncIdGenerator:
    """Async ID generator using segment allocation"""

    def __init__(
        self,
        segment_client: SegmentClient,
        system_code: str,
        db_name: str,
        table_name: str,
        field_name: str,
        segment_count: int = 10000
    ):
        """
        Initialize the AsyncIdGenerator.

        Args:
            segment_client: SegmentClient instance for allocating segments
            system_code: System code
            db_name: Database name
            table_name: Table name
            field_name: Field name
            segment_count: Number of IDs to allocate per segment (default: 10000)
        """
        self.segment_client = segment_client
        self.system_code = system_code
        self.db_name = db_name
        self.table_name = table_name
        self.field_name = field_name
        self.segment_count = segment_count

        self._lock = asyncio.Lock()
        self._current: Optional[int] = None
        self._end: Optional[int] = None

    async def _allocate_new_segment(self) -> None:
        """Allocate a new segment asynchronously (must be called with lock held)"""
        segment = await self.segment_client.allocate_segment_async(
            system_code=self.system_code,
            db_name=self.db_name,
            table_name=self.table_name,
            field_name=self.field_name,
            segment_count=self.segment_count
        )
        self._current = segment.start
        self._end = segment.end

    async def next_id(self) -> int:
        """
        Generate next ID asynchronously in a coroutine-safe manner.

        Returns:
            int: The next available ID

        Raises:
            OpenIdAPIError: If the API returns an error response
            OpenIdConnectionError: If connection to the API fails
            OpenIdTimeoutError: If the request times out
        """
        async with self._lock:
            # Check if we need to allocate a segment
            if self._current is None or self._end is None:
                await self._allocate_new_segment()
            # Check if current segment is exhausted
            elif self._current > self._end:
                await self._allocate_new_segment()

            # Get current ID and increment
            current_id = self._current
            self._current += 1
            return current_id
