import json
from operator import itemgetter

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from vidoso.repo.segments import SegmentsRepo


class SearchService:
    def __init__(
        self,
        segments_repo: SegmentsRepo,
        sentence_transformer: SentenceTransformer,
    ) -> None:
        self.segments_repo = segments_repo
        self.sentence_transformer = sentence_transformer

    async def search(
        self,
        user: str,
        k: int,
        text: list[str],
        embeddings: list[str],
        exclude_embeddings: bool = True,
    ) -> dict:
        # TODO: this method needs some love

        segments_db = await self.segments_repo.get_multi_by_user(user=user)
        if not segments_db.segments:
            return None

        segments_embeddings = np.array(
            [
                np.array(json.loads(segment.embedding), dtype=np.float32)
                for segment in segments_db.segments
            ]
        )
        dim = segments_embeddings.shape[1]

        if text:
            query_text_embeddings = self.sentence_transformer.encode(text)
        else:
            query_text_embeddings = np.array([], dtype=np.float32).reshape(0, dim)

        if embeddings:
            query_raw_embeddings = np.array(
                [
                    np.array(json.loads(embedding), dtype=np.float32)
                    for embedding in embeddings
                ]
            )
        else:
            query_raw_embeddings = np.array([], dtype=np.float32).reshape(0, dim)

        query_embeddings = np.vstack([query_text_embeddings, query_raw_embeddings])

        faiss.normalize_L2(query_embeddings)
        faiss.normalize_L2(segments_embeddings)

        index = faiss.IndexFlatL2(dim)
        index.add(segments_embeddings)
        distances, ann = index.search(query_embeddings, k=k)

        text_search_segments = (
            [
                itemgetter(*a)(segments_db.segments)
                for a in ann[: query_text_embeddings.shape[0]]
            ]
            if query_text_embeddings.shape[0]
            else []
        )
        embeddings_search_segments = (
            [
                itemgetter(*a)(segments_db.segments)
                for a in ann[-query_raw_embeddings.shape[0] :]
            ]
            if query_raw_embeddings.shape[0]
            else []
        )
        results = {
            "text": [
                [
                    s.model_dump(
                        **({"exclude": ["embedding"]} if exclude_embeddings else {})
                    )
                    for s in row
                ]
                for row in text_search_segments
            ],
            "embeddings": [
                [
                    s.model_dump(
                        **({"exclude": ["embedding"]} if exclude_embeddings else {})
                    )
                    for s in row
                ]
                for row in embeddings_search_segments
            ],
        }
        return results


# factories


async def search_service_fct(
    segments_repo: SegmentsRepo,
    sentence_transformer: SentenceTransformer,
) -> SearchService:
    search_svc = SearchService(
        segments_repo=segments_repo,
        sentence_transformer=sentence_transformer,
    )
    return search_svc
