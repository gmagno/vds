from functools import lru_cache
from typing import Annotated

import boto3
import whisper
from fastapi import Depends
from mypy_boto3_dynamodb.client import DynamoDBClient
from sentence_transformers import SentenceTransformer
from whisper import Whisper

from vidoso.config import Settings
from vidoso.repo.jobs import JobsRepo, jobs_repo_fct
from vidoso.repo.segments import SegmentsRepo, segments_repo_fct
from vidoso.services.search import SearchService, search_service_fct
from vidoso.services.stream_processor import (
    StreamProcessorService,
    stream_processor_service_fct,
)

# settings


@lru_cache
def get_settings_dep() -> Settings:
    settings = Settings()
    return settings


# whisper


def get_whisper_model_dep(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> Whisper:
    whisper_model: Whisper = whisper.load_model(settings.whisper_model)
    return whisper_model


def get_sentence_transformer_dep(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> SentenceTransformer:
    sentence_transformer = SentenceTransformer(settings.sentence_transformer_model)
    return sentence_transformer


sentence_transformer_model = SentenceTransformer("paraphrase-mpnet-base-v2")


# aws dynamodb / repos


def get_dynamodb_client_dep() -> DynamoDBClient:
    dynamodb_client = boto3.client("dynamodb")
    return dynamodb_client


async def get_jobs_repo_dep(
    dynamodb_client: Annotated[DynamoDBClient, Depends(get_dynamodb_client_dep)],
) -> JobsRepo:
    jobs_repo = await jobs_repo_fct(dynamodb_client=dynamodb_client)
    return jobs_repo


async def get_segments_repo_dep(
    dynamodb_client: Annotated[DynamoDBClient, Depends(get_dynamodb_client_dep)],
) -> SegmentsRepo:
    segments_repo = await segments_repo_fct(dynamodb_client=dynamodb_client)
    return segments_repo


# services


async def get_stream_processor_service_dep(
    jobs_repo: Annotated[JobsRepo, Depends(get_jobs_repo_dep)],
    segments_repo: Annotated[SegmentsRepo, Depends(get_segments_repo_dep)],
    whisper_model: Annotated[Whisper, Depends(get_whisper_model_dep)],
    sentence_transformer: Annotated[
        SentenceTransformer, Depends(get_sentence_transformer_dep)
    ],
) -> StreamProcessorService:
    stream_processor_svc = await stream_processor_service_fct(
        jobs_repo=jobs_repo,
        segments_repo=segments_repo,
        whisper_model=whisper_model,
        sentence_transformer=sentence_transformer,
    )
    return stream_processor_svc


async def get_search_service_dep(
    segments_repo: Annotated[SegmentsRepo, Depends(get_segments_repo_dep)],
    sentence_transformer: Annotated[
        SentenceTransformer, Depends(get_sentence_transformer_dep)
    ],
) -> SearchService:
    search_svc = await search_service_fct(
        segments_repo=segments_repo,
        sentence_transformer=sentence_transformer,
    )
    return search_svc
