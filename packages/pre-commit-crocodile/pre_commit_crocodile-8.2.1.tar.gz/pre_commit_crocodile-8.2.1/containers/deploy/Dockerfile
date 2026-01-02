ARG IMAGE_BASE=python:3-alpine
FROM $IMAGE_BASE

# Install dependencies
RUN apk add -q --no-cache  \
      gcc \
      git \
      libc-dev \
      libffi-dev \
      sed

# Install requirements
COPY --from='requirements' ./deploy.txt /tmp/
RUN export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q -r /tmp/deploy.txt --no-cache-dir --upgrade \
 && rm -f /tmp/deploy.txt
