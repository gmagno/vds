import asyncio
import datetime as dt
import json
import os
import tempfile
from uuid import uuid4

from pytube import YouTube
from sentence_transformers import SentenceTransformer
from whisper import Whisper

from vidoso.core.logger import logger
from vidoso.repo.jobs import JobsRepo
from vidoso.repo.schemas import SegmentDb
from vidoso.repo.segments import SegmentsRepo


class StreamProcessorService:
    def __init__(
        self,
        jobs_repo: JobsRepo,
        segments_repo: SegmentsRepo,
        whisper_model: Whisper,
        sentence_transformer: str,
    ) -> None:
        self.jobs_repo = jobs_repo
        self.whisper_model = whisper_model
        self.segments_repo = segments_repo
        self.sentence_transformer = sentence_transformer

    def download_and_transcribe_audio_stream(self, stream_url: str) -> dict:
        logger.info(f"download_and_transcribe_audio_stream [{stream_url=}]")
        yt = YouTube(stream_url)
        audio_streams = yt.streams.filter(only_audio=True)

        # extract the first audio stream
        stream = audio_streams.get_by_itag(itag=audio_streams[0].itag)

        with tempfile.NamedTemporaryFile() as temp:
            dirname = os.path.dirname(temp.name)
            filename = os.path.basename(temp.name)
            stream.download(output_path=dirname, filename=filename)
            transcript = self.whisper_model.transcribe(temp.name, language="en")
        return transcript

    async def process_stream(self, stream_url: str) -> None:
        logger.info(f"process_stream [{stream_url=}]")
        transcript = self.download_and_transcribe_audio_stream(stream_url=stream_url)

        transcript_id = str(uuid4())
        now = dt.datetime.now()
        segments_texts = [segment["text"] for segment in transcript["segments"]]
        embeddings = self.sentence_transformer.encode(segments_texts)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    self.segments_repo.upsert(
                        segment=SegmentDb(
                            transcript_id=transcript_id,
                            segment_id=segment["id"],
                            user="anonymous",
                            created_at=now,
                            stream_url=stream_url,
                            start=segment["start"],
                            end=segment["end"],
                            text=segment["text"],
                            embedding=json.dumps(embeddings[i].tolist()),
                        )
                    )
                )
                for i, segment in enumerate(transcript["segments"])
            ]
        segments_db_upserted = [t.result() for t in tasks]

        segments_db_upserted_excluding_embedding = [
            s.model_dump(exclude=["embedding"]) for s in segments_db_upserted
        ]
        logger.info(f"segments added [{segments_db_upserted_excluding_embedding=}]")


# factories


async def stream_processor_service_fct(
    jobs_repo: JobsRepo,
    segments_repo: SegmentsRepo,
    whisper_model: Whisper,
    sentence_transformer: SentenceTransformer,
) -> StreamProcessorService:
    stream_processor_svc = StreamProcessorService(
        jobs_repo=jobs_repo,
        segments_repo=segments_repo,
        whisper_model=whisper_model,
        sentence_transformer=sentence_transformer,
    )
    return stream_processor_svc
