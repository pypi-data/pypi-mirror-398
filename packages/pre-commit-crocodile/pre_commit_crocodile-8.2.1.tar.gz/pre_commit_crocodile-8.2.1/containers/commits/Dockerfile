ARG IMAGE_BASE=python:3-alpine
FROM $IMAGE_BASE

# Install dependencies
RUN apk add -q --no-cache  \
      bash \
      coreutils \
      gcc \
      git \
      git-lfs \
      libc-dev

# Install requirements
COPY --from='requirements' ./commits.txt /tmp/
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=cache,target=/root/.rustup \
    export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q -r /tmp/commits.txt --no-cache-dir --upgrade \
 && rm -f /tmp/commits.txt

# Create image version
ARG IMAGE_VERSION=7
RUN echo -n "${IMAGE_VERSION}" >/VERSION
