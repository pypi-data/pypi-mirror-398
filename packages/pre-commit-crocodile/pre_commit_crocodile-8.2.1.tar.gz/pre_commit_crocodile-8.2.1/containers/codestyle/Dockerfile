ARG IMAGE_BASE=python:3-alpine
FROM $IMAGE_BASE

# Install dependencies
RUN apk add -q --no-cache  \
      gcc \
      git \
      libc-dev

# Install requirements
COPY --from='requirements' ./runtime.txt /tmp/
COPY --from='requirements' ./quality.txt /tmp/
COPY --from='requirements' ./tests.txt /tmp/
RUN export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q -r /tmp/runtime.txt --no-cache-dir --upgrade \
 && pip3 install -q -r /tmp/quality.txt --no-cache-dir --upgrade \
 && pip3 install -q -r /tmp/tests.txt --no-cache-dir --upgrade \
 && rm -f /tmp/runtime.txt \
 && rm -f /tmp/quality.txt \
 && rm -f /tmp/tests.txt
