"""
Data models for kxy-open-id-client
"""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field


T = TypeVar('T')


class SegmentRequest(BaseModel):
    """Request model for ID segment allocation"""
    system_code: str = Field(..., description="System code")
    db_name: str = Field(..., description="Database name")
    table_name: str = Field(..., description="Table name")
    field_name: str = Field(..., description="Field name")
    segment_count: int = Field(10000, ge=1, le=9223372036854775807, description="Segment count (max: 2^63-1)")


class SegmentResponse(BaseModel):
    """Response model for ID segment allocation"""
    start: int = Field(..., description="Start ID of segment")
    end: int = Field(..., description="End ID of segment")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper"""
    code: int = 0
    msg: str = ""
    data: Optional[T] = None
    traceId: Optional[str] = None
