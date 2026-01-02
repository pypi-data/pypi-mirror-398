ARG IMAGE_BASE=python:3-alpine
FROM $IMAGE_BASE

# Install dependencies
RUN apk add -q --no-cache  \
      bash \
      docker \
      git \
      nano \
      util-linux-misc

# Install requirements
COPY --from='requirements' ./docs.txt /tmp/
COPY --from='requirements' ./tests.txt /tmp/
RUN export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q -r /tmp/docs.txt --no-cache-dir --upgrade \
 && pip3 install -q -r /tmp/tests.txt --no-cache-dir --upgrade \
 && pipx ensurepath \
 && rm -f /tmp/docs.txt \
 && rm -f /tmp/tests.txt
