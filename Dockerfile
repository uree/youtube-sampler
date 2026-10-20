FROM alpine:3.21

RUN apk add --no-cache \
        ffmpeg \
        bash \
        python3 \
        py3-pip \
    && apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev \
        openssl-dev

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apk del .build-deps

WORKDIR /home/youtube_sampler
RUN mkdir -p app/logs app/files
COPY app/ ./app/
COPY run.py .

EXPOSE 420

CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:420", "-t", "90"]
