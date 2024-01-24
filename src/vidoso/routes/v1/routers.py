import asyncio
import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Response, status

from vidoso import worker
from vidoso.config import Settings
from vidoso.deps import (
    get_jobs_repo_dep,
    get_search_service_dep,
    get_segments_repo_dep,
    get_settings_dep,
    get_stream_processor_service_dep,
)
from vidoso.repo.jobs import JobsRepo
from vidoso.repo.schemas import JobDb, JobStatus
from vidoso.repo.segments import SegmentsRepo
from vidoso.routes.v1.schemas import (
    HealthCheck,
    JobRead,
    JobsCreate,
    JobsRead,
    SearchQuery,
    SearchQueryResponse,
    SegmentsRead,
)
from vidoso.services.search import SearchService
from vidoso.services.stream_processor import StreamProcessorService

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def health_check() -> HealthCheck:
    return HealthCheck()


# jobs


@router.post(
    "/user-jobs",
    status_code=status.HTTP_200_OK,
)
async def create_job(
    jobs_repo: Annotated[JobsRepo, Depends(get_jobs_repo_dep)],
    jobs_create: Annotated[JobsCreate, Body],
) -> JobsRead:
    now = dt.datetime.now()
    jobs_db = [
        JobDb.model_validate(
            job.model_dump() | {"created_at": now, "status": JobStatus.PROCESSING}
        )
        for job in jobs_create.jobs
    ]
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(jobs_repo.upsert(job=job)) for job in jobs_db]
    jobs_db_upserted = [t.result() for t in tasks]
    jobs_read = JobsRead(
        jobs=[
            JobRead.model_validate(job, from_attributes=True)
            for job in jobs_db_upserted
        ]
    )

    for job in jobs_db_upserted:
        worker.process_video_stream(job_id=job.job_id)

    return jobs_read


@router.get(
    "/user-jobs",
    response_model=JobsRead,
    response_model_exclude_none=True,
)
async def list_user_jobs(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    jobs_repo: Annotated[JobsRepo, Depends(get_jobs_repo_dep)],
    user: Annotated[
        str,
        Query(description="Constrain jobs to a specific user"),
    ] = "anonymous",
    created_after: Annotated[
        dt.datetime | None,
        Query(description="Filter jobs by timestamp greater than or equal"),
    ] = None,
    created_before: Annotated[
        dt.datetime | None,
        Query(description="Filter jobs by timestamp less than or equal"),
    ] = None,
) -> JobsRead:
    jobs_db = await jobs_repo.get_multi_by_user(
        user=user,
        created_after=created_after,
        created_before=created_before,
    )
    jobs = JobsRead.model_validate(jobs_db, from_attributes=True)
    return jobs


# segments


@router.get(
    "/user-segments",
    response_model=SegmentsRead,
    response_model_exclude_none=True,
)
async def list_user_segments(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    segments_repo: Annotated[SegmentsRepo, Depends(get_segments_repo_dep)],
    user: Annotated[
        str,
        Query(description="Constrain segments to a specific user"),
    ] = "anonymous",
    created_after: Annotated[
        dt.datetime | None,
        Query(description="Filter segments by timestamp greater than or equal"),
    ] = None,
    created_before: Annotated[
        dt.datetime | None,
        Query(description="Filter segments by timestamp less than or equal"),
    ] = None,
    exclude_embeddings: Annotated[
        bool,
        Query(description="Whether to exclude the segment embedding, for readability"),
    ] = True,
) -> SegmentsRead:
    segments_db = await segments_repo.get_multi_by_user(
        user=user,
        created_after=created_after,
        created_before=created_before,
    )
    segments = [
        segment.model_dump(**({"exclude": ["embedding"]} if exclude_embeddings else {}))
        for segment in segments_db.segments
    ]
    segments_read = SegmentsRead.model_validate({"segments": segments})
    return segments_read


@router.post(
    "/dev-process-streams",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def dev_process_streams(
    stream_processor_svc: Annotated[
        StreamProcessorService, Depends(get_stream_processor_service_dep)
    ],
    stream_url: str,
) -> None:
    await stream_processor_svc.process_stream(stream_url=stream_url)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
    response_model=SearchQueryResponse,
    response_model_exclude_none=True,
)
async def search(
    search_svc: Annotated[SearchService, Depends(get_search_service_dep)],
    search_query: Annotated[SearchQuery, Body],
) -> SearchQueryResponse:
    if not search_query.text and not search_query.embeddings:
        return SearchQueryResponse(text=[], embeddings=[])

    results = await search_svc.search(
        user=search_query.user,
        k=search_query.k,
        text=search_query.text,
        embeddings=search_query.embeddings,
        exclude_embeddings=search_query.exclude_embeddings,
    )
    search_query_response = SearchQueryResponse.model_validate(results)
    return search_query_response
