import asyncio

from huey import RedisHuey

from vidoso.core.logger import logger
from vidoso.deps import (
    get_dynamodb_client_dep,
    get_jobs_repo_dep,
    get_segments_repo_dep,
    get_sentence_transformer_dep,
    get_settings_dep,
    get_whisper_model_dep,
)
from vidoso.repo.schemas import JobStatus
from vidoso.services.stream_processor import stream_processor_service_fct

huey: RedisHuey = RedisHuey(
    "worker",
    immediate=False,
    host="redis",
)


async def a_process_video_stream(job_id: str) -> None:
    logger.info(f"a_process_video_stream [{job_id=}]")

    settings = get_settings_dep()
    dynamodb_client = get_dynamodb_client_dep()
    whisper_model = get_whisper_model_dep(settings=settings)
    sentence_transformer = get_sentence_transformer_dep(settings=settings)
    jobs_repo = await get_jobs_repo_dep(dynamodb_client=dynamodb_client)
    segments_repo = await get_segments_repo_dep(dynamodb_client=dynamodb_client)

    job_db = await jobs_repo.get_by_job_id(job_id=job_id)

    stream_processor_svc = await stream_processor_service_fct(
        jobs_repo=jobs_repo,
        segments_repo=segments_repo,
        whisper_model=whisper_model,
        sentence_transformer=sentence_transformer,
    )
    await stream_processor_svc.process_stream(job_db.stream_url)
    job_db.status = JobStatus.DONE
    await jobs_repo.upsert(job=job_db)
    logger.info(
        f"a_process_video_stream done! [{job_db.model_dump(exclude=['embedding'])=}]"
    )


@huey.task()
def process_video_stream(job_id: str) -> None:
    asyncio.run(a_process_video_stream(job_id=job_id))
