import asyncio
import datetime as dt
from functools import partial
from typing import Any

from boto3.dynamodb.conditions import ConditionExpressionBuilder, Key
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from mypy_boto3_dynamodb.client import DynamoDBClient

from vidoso.core.logger import logger
from vidoso.repo.schemas import SegmentDb, SegmentsDb

TABLE_NAME = "segments"

KEY_ATTRIBUTES = ["transcript_id", "segment_id"]

SERIALIZER = TypeSerializer()
DESERIALIZER = TypeDeserializer()


class SegmentsRepo:
    def __init__(
        self,
        dynamodb_client: DynamoDBClient,
    ) -> None:
        self.dynamodb_client = dynamodb_client

    def deserialize_values(
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        return {k: DESERIALIZER.deserialize(value=v) for k, v in item.items()}

    def serialize_values(
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        return {k: SERIALIZER.serialize(value=v) for k, v in item.items()}

    async def get_multi_by_transcript_id(
        self,
        transcript_id: str,
    ) -> SegmentsDb:
        logger.info(f"get_multi_by_transcript_id {transcript_id=}")

        key_cond = Key("transcript_id").eq(transcript_id)

        builder = ConditionExpressionBuilder()
        expr = builder.build_expression(key_cond, is_key_condition=True)

        get_items = partial(
            self.dynamodb_client.query,
            TableName=TABLE_NAME,
            # IndexName="user-index",
            KeyConditionExpression=expr.condition_expression,
            ExpressionAttributeNames=expr.attribute_name_placeholders,
            ExpressionAttributeValues=self.serialize_values(
                expr.attribute_value_placeholders
            ),
        )
        response = await asyncio.to_thread(get_items)
        results = [
            SegmentDb.model_validate(self.deserialize_values(item))
            for item in response["Items"]
        ]
        segments = SegmentsDb(segments=results)
        return segments

    async def get_multi_by_user(
        self,
        user: str,
        created_after: dt.datetime | None = None,
        created_before: dt.datetime | None = None,
    ) -> SegmentsDb:
        logger.info(f"get_multi_by_user {user=}")

        start = int(created_after.timestamp()) if created_after else 0
        end = int(created_before.timestamp()) if created_before else None

        key_cond = Key("user").eq(user)
        if end is None:
            key_cond &= Key("created_at").gte(start)
        else:
            key_cond &= Key("created_at").between(start, end)

        builder = ConditionExpressionBuilder()
        expr = builder.build_expression(key_cond, is_key_condition=True)

        get_items = partial(
            self.dynamodb_client.query,
            TableName=TABLE_NAME,
            IndexName="user-index",
            KeyConditionExpression=expr.condition_expression,
            ExpressionAttributeNames=expr.attribute_name_placeholders,
            ExpressionAttributeValues=self.serialize_values(
                expr.attribute_value_placeholders
            ),
        )
        response = await asyncio.to_thread(get_items)
        results = [
            SegmentDb.model_validate(self.deserialize_values(item))
            for item in response["Items"]
        ]
        results.sort(key=lambda x: (x.created_at, x.segment_id))
        segments = SegmentsDb(segments=results)
        return segments

    async def upsert(
        self,
        segment: SegmentDb,
        fail_if_exists: bool = False,
    ) -> SegmentDb:
        segment_dump = segment.model_dump(exclude_none=True)
        segment_dump_excluding_embedding = segment.model_dump(exclude=["embedding"])
        logger.info(f"segment {segment_dump_excluding_embedding=}")
        indexed_attrs = list(enumerate(segment_dump.items()))
        update_expr = ", ".join(
            f"#k{i}=:v{i}" for i, (k, v) in indexed_attrs if k not in KEY_ATTRIBUTES
        )
        names = {f"#k{i}": k for i, (k, v) in indexed_attrs if k not in KEY_ATTRIBUTES}
        values = {
            f":v{i}": SERIALIZER.serialize(v)
            for i, (k, v) in indexed_attrs
            if k not in KEY_ATTRIBUTES
        }

        condition_expression = (
            {"ConditionExpression": "attribute_not_exists(segment_id)"}
            if fail_if_exists
            else {}
        )
        update_func = partial(
            self.dynamodb_client.update_item,
            TableName=TABLE_NAME,
            Key={
                "transcript_id": SERIALIZER.serialize(segment_dump["transcript_id"]),
                "segment_id": SERIALIZER.serialize(segment_dump["segment_id"]),
            },
            UpdateExpression=f"SET {update_expr}",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            **condition_expression,
        )
        await asyncio.to_thread(update_func)
        return segment


# factories


async def segments_repo_fct(
    dynamodb_client: DynamoDBClient,
) -> SegmentsRepo:
    segments_repo = SegmentsRepo(dynamodb_client=dynamodb_client)
    return segments_repo
