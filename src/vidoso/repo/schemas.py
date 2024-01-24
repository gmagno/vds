import datetime as dt
from decimal import Decimal
from enum import StrEnum, auto

from pydantic import BaseModel, field_serializer


class JobStatus(StrEnum):
    PROCESSING = auto()
    DONE = auto()


class JobDb(BaseModel):
    job_id: str | None = None
    user: str
    created_at: dt.datetime
    status: JobStatus
    stream_url: str

    @field_serializer("created_at")
    def serialize_dt(self, created_at: dt.datetime) -> float:
        return Decimal(created_at.timestamp())


class JobsDb(BaseModel):
    jobs: list[JobDb]


# -------------#


class SegmentDb(BaseModel):
    transcript_id: str
    segment_id: int
    user: str
    created_at: dt.datetime
    stream_url: str
    start: Decimal
    end: Decimal
    text: str
    embedding: str

    @field_serializer("created_at")
    def serialize_dt(self, created_at: dt.datetime) -> Decimal:
        return Decimal(created_at.timestamp())


class SegmentsDb(BaseModel):
    segments: list[SegmentDb]
