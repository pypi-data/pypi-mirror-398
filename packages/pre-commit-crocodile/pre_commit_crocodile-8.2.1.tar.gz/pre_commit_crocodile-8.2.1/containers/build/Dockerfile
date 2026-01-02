ARG IMAGE_BASE=python:3-alpine
FROM $IMAGE_BASE

# Install dependencies
RUN apk add -q \
      gcc \
      git \
      libc-dev

# Install requirements
COPY --from='requirements' ./runtime.txt /tmp/
COPY --from='requirements' ./build.txt /tmp/
RUN export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q -r /tmp/runtime.txt --no-cache-dir --upgrade \
 && pip3 install -q -r /tmp/build.txt --no-cache-dir --upgrade \
 && rm -f /tmp/runtime.txt \
 && rm -f /tmp/build.txt
