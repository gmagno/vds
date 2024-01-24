# Vidoso

* [Description](#description)
* [Usage](#usage)

## Description

An api for text semantic search.

Services:

- [api](https://github.com/tiangolo/fastapi): fastpi app
- [huey](https://github.com/coleifer/huey) task queue/worker: cpu bound tasks: audio streams processing

## Deps

- docker/docker-compose
- make


## Build images

    make infra-build


## Create tables and indexes

    make db-local-admin-create-tables
    make db-local-admin-create-indexes

## Run app

    make infra-run

## Tail logs

    make infra-logs


## OpenAPI docs

    Check openapi generated docs at: <http://127.0.0.1:9000/vidoso/v1/docs>

## Usage

Process multiple streams in parallel:

```bash
curl -X 'POST' \
  'http://127.0.0.1:9000/vidoso/v1/user-jobs' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "jobs": [
    {
      "user": "anonymous",
      "stream_url": "https://www.youtube.com/shorts/oJbJ9SaxJ54"
    },
    {
      "user": "anonymous",
      "stream_url": "https://www.youtube.com/shorts/tJXAwgqvLeg"
    }
  ]
}'
```

which should respond with:

```json
{
  "jobs": [
    {
      "user": "anonymous",
      "job_id": "fdbf9b35-173d-4d00-9b5f-787aec9cf0d0",
      "created_at": "2024-01-24T13:55:12.948721",
      "status": "processing"
    },
    {
      "user": "anonymous",
      "job_id": "9836da9d-c19a-45cf-bfb4-77be23547f42",
      "created_at": "2024-01-24T13:55:12.948721",
      "status": "processing"
    }
  ]
}
```

Check the jobs status `processing` -> `done`:

```
curl -X 'GET' \
  'http://127.0.0.1:9000/vidoso/v1/user-jobs?user=anonymous' \
  -H 'accept: application/json'
```

```json
{
  "jobs": [
    {
      "user": "anonymous",
      "job_id": "fdbf9b35-173d-4d00-9b5f-787aec9cf0d0",
      "created_at": "2024-01-24T13:55:12.948721",
      "status": "processing"
    },
    {
      "user": "anonymous",
      "job_id": "9836da9d-c19a-45cf-bfb4-77be23547f42",
      "created_at": "2024-01-24T13:55:12.948721",
      "status": "done"
    }
  ]
}
```

## Search for text

Search for the text: `chris`:

```bash
curl -X 'POST' \
  'http://127.0.0.1:9000/vidoso/v1/search' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user": "anonymous",
  "k": 3,
  "text": [
    "chris"
  ],
  "embeddings": [
  ],
  "exclude_embeddings": true
}'
```

## Search also works with embeddings

Search with a vector:

```bash
curl -X 'POST' \
  'http://127.0.0.1:9000/vidoso/v1/search' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user": "anonymous",
  "k": 3,
  "text": [
    "chris",
    "batman"
  ],
  "embeddings": [
    "[0.11550885438919067, 0.20192337036132812, ..., -0.06627673655748367]",
  ],
  "exclude_embeddings": true
}'
```

```json
{
  "text": [
    [
      {
        "transcript_id": "8e9e6b9f-aa8e-4f32-9bf1-6f7ef1f4875a",
        "segment_id": 3,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:27.961400Z",
        "stream_url": "https://www.youtube.com/shorts/oJbJ9SaxJ54",
        "start": "14.72",
        "end": "19.36",
        "text": " And we were like, every time Chris was going to, Chris no longer the director was going, guys, you know?"
      },
      {
        "transcript_id": "155cbaf3-1c72-4fe5-ae78-95d81d6785d0",
        "segment_id": 12,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:29.811871Z",
        "stream_url": "https://www.youtube.com/shorts/tJXAwgqvLeg",
        "start": "34.32",
        "end": "36.64",
        "text": " against Stokes City at Britannia?"
      },
      {
        "transcript_id": "155cbaf3-1c72-4fe5-ae78-95d81d6785d0",
        "segment_id": 11,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:29.811871Z",
        "stream_url": "https://www.youtube.com/shorts/tJXAwgqvLeg",
        "start": "31.040000000000003",
        "end": "34.32",
        "text": " Now, do you think Messi could survive a rainy Tuesday night"
      }
    ],
    [
      {
        "transcript_id": "155cbaf3-1c72-4fe5-ae78-95d81d6785d0",
        "segment_id": 6,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:29.811871Z",
        "stream_url": "https://www.youtube.com/shorts/tJXAwgqvLeg",
        "start": "14.32",
        "end": "18.080000000000002",
        "text": " Messi is basically a system player"
      },
      {
        "transcript_id": "155cbaf3-1c72-4fe5-ae78-95d81d6785d0",
        "segment_id": 1,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:29.811871Z",
        "stream_url": "https://www.youtube.com/shorts/tJXAwgqvLeg",
        "start": "2.0",
        "end": "4.5600000000000005",
        "text": " People always say, oh, but Messi is better."
      },
      {
        "transcript_id": "155cbaf3-1c72-4fe5-ae78-95d81d6785d0",
        "segment_id": 5,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:29.811871Z",
        "stream_url": "https://www.youtube.com/shorts/tJXAwgqvLeg",
        "start": "12.32",
        "end": "14.32",
        "text": " Messi has destroyed what exactly?"
      }
    ]
  ],
  "embeddings": [
    [
      {
        "transcript_id": "8e9e6b9f-aa8e-4f32-9bf1-6f7ef1f4875a",
        "segment_id": 3,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:27.961400Z",
        "stream_url": "https://www.youtube.com/shorts/oJbJ9SaxJ54",
        "start": "14.72",
        "end": "19.36",
        "text": " And we were like, every time Chris was going to, Chris no longer the director was going, guys, you know?"
      },
      {
        "transcript_id": "8e9e6b9f-aa8e-4f32-9bf1-6f7ef1f4875a",
        "segment_id": 7,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:27.961400Z",
        "stream_url": "https://www.youtube.com/shorts/oJbJ9SaxJ54",
        "start": "30.400000000000002",
        "end": "33.2",
        "text": " And then he would do his bit and then he'd go like that."
      },
      {
        "transcript_id": "8e9e6b9f-aa8e-4f32-9bf1-6f7ef1f4875a",
        "segment_id": 0,
        "user": "anonymous",
        "created_at": "2024-01-24T15:38:27.961400Z",
        "stream_url": "https://www.youtube.com/shorts/oJbJ9SaxJ54",
        "start": "0.0",
        "end": "6.24",
        "text": " You know, the thing that would happen between me and Tom, who's superb, by the way, one acted."
      }
    ]
  ]
}
```

## Tests

:)
