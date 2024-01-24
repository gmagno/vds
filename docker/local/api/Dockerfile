FROM python:3.11.6-bullseye

ENV USER_ID=1001
ENV GROUP_ID=1001
ENV USER_NAME=app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN groupadd -g ${GROUP_ID} ${USER_NAME}
RUN useradd ${USER_NAME} -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash

RUN apt-get -y update && apt-get -y upgrade && apt-get install -y ffmpeg

COPY --chown=${USER_ID}:${GROUP_ID} ./requirements-dev.txt /requirements/

RUN pip install -U pip && \
    pip install -r /requirements/requirements-dev.txt

COPY --chown=${USER_ID}:${GROUP_ID} ./docker/local/api/entrypoint /entrypoint
COPY --chown=${USER_ID}:${GROUP_ID} ./docker/local/api/start /start
COPY --chown=${USER_ID}:${GROUP_ID} ./docker/local/huey/start-worker /start-worker

RUN chmod +x /entrypoint && \
    chmod +x /start && \
    chmod +x /start-worker

WORKDIR /app/
USER ${USER_NAME}

ENTRYPOINT [ "/entrypoint" ]
