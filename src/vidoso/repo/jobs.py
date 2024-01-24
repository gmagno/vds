import asyncio
import datetime as dt
from functools import partial
from typing import Any
from uuid import uuid4

from boto3.dynamodb.conditions import ConditionExpressionBuilder, Key
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from mypy_boto3_dynamodb.client import DynamoDBClient

from vidoso.core.logger import logger
from vidoso.repo.schemas import JobDb, JobsDb

TABLE_NAME = "jobs"

KEY_ATTRIBUTES = ["job_id", "created_at"]

SERIALIZER = TypeSerializer()
DESERIALIZER = TypeDeserializer()


class JobsRepo:
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

    async def get_by_job_id(
        self,
        job_id: str,
    ) -> JobDb:
        logger.info(f"get_by_job_id {job_id=}")

        key_cond = Key("job_id").eq(job_id)
        builder = ConditionExpressionBuilder()
        expr = builder.build_expression(key_cond, is_key_condition=True)

        get_items = partial(
            self.dynamodb_client.query,
            TableName=TABLE_NAME,
            KeyConditionExpression=expr.condition_expression,
            ExpressionAttributeNames=expr.attribute_name_placeholders,
            ExpressionAttributeValues=self.serialize_values(
                expr.attribute_value_placeholders
            ),
        )
        response = await asyncio.to_thread(get_items)
        job = JobDb.model_validate(self.deserialize_values(response["Items"][0]))
        return job

    async def get_multi_by_user(
        self,
        user: str,
        created_after: dt.datetime | None = None,
        created_before: dt.datetime | None = None,
    ) -> JobsDb:
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
            JobDb.model_validate(self.deserialize_values(item))
            for item in response["Items"]
        ]
        jobs = JobsDb(jobs=results)
        return jobs

    async def upsert(
        self,
        job: JobDb,
        fail_if_exists: bool = False,
    ) -> JobDb:
        if not job.job_id:
            job.job_id = str(uuid4())
        job_dump = job.model_dump(exclude_none=True)
        logger.info(f"job {job_dump=}")
        indexed_attrs = list(enumerate(job_dump.items()))
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
            {"ConditionExpression": "attribute_not_exists(job_id)"}
            if fail_if_exists
            else {}
        )
        update_func = partial(
            self.dynamodb_client.update_item,
            TableName=TABLE_NAME,
            Key={
                "job_id": SERIALIZER.serialize(job_dump["job_id"]),
                "created_at": SERIALIZER.serialize(job_dump["created_at"]),
            },
            UpdateExpression=f"SET {update_expr}",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            **condition_expression,
        )
        await asyncio.to_thread(update_func)
        return job


# factories


async def jobs_repo_fct(
    dynamodb_client: DynamoDBClient,
) -> JobsRepo:
    jobs_repo = JobsRepo(dynamodb_client=dynamodb_client)
    return jobs_repo
