"""
Client implementation for KXY Open ID Service
"""

import httpx
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
