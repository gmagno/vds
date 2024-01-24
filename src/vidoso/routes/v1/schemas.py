import datetime as dt
from enum import StrEnum, auto
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthCheck(BaseModel):
    status: Literal["OK"] = "OK"


# job


class JobStatus(StrEnum):
    PROCESSING = auto()
    DONE = auto()


class JobBase(BaseModel):
    user: str


class JobRead(JobBase):
    # model_config = ConfigDict(populate_by_name=True)

    job_id: str
    created_at: Annotated[dt.datetime, Field(examples=["2023-10-24T11:30:00"])]
    status: JobStatus


class JobCreate(JobBase):
    user: str | None = "anonymous"
    stream_url: str


class JobsRead(BaseModel):
    jobs: list[JobRead]


class JobsCreate(BaseModel):
    jobs: list[JobCreate]


# segment


class SegmentRead(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    transcript_id: str
    segment_id: int
    user: str
    created_at: Annotated[dt.datetime, Field(examples=["2023-10-24T11:30:00"])]
    stream_url: str
    start: str
    end: str
    text: str
    embedding: str | None = None


class SegmentsRead(BaseModel):
    segments: list[SegmentRead]


# search


class SearchQuery(BaseModel):
    user: Annotated[
        str,
        Field(description="Constrain search to segments from a specific user"),
    ] = "anonymous"
    k: Annotated[
        int,
        Field(description="Pick the top `k` results", ge=2),
    ] = 3
    text: list[str]
    embeddings: list[str]
    exclude_embeddings: Annotated[
        bool,
        Field(description="Whether to exclude the segment embedding, for readability"),
    ] = True


class SearchQueryResponse(BaseModel):
    text: list[list[SegmentRead]]
    embeddings: list[list[SegmentRead]]
