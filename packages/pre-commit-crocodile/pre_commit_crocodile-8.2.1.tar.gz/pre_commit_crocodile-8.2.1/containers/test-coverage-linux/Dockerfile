ARG IMAGE_BASE=python:3
FROM $IMAGE_BASE

# Install dependencies
RUN apt-get update -qq \
 && apt-get install -qq -y sudo time 2>&1 | grep 'Setting up' \
 && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY --from='requirements' ./runtime.txt /tmp/
COPY --from='requirements' ./coverage.txt /tmp/
COPY --from='requirements' ./tests.txt /tmp/
RUN export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q -r /tmp/runtime.txt --no-cache-dir --upgrade \
 && pip3 install -q -r /tmp/coverage.txt --no-cache-dir --upgrade \
 && pip3 install -q -r /tmp/tests.txt --no-cache-dir --upgrade \
 && rm -f /tmp/runtime.txt \
 && rm -f /tmp/coverage.txt \
 && rm -f /tmp/tests.txt
