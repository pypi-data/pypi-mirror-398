ARG IMAGE_BASE=python:3
FROM $IMAGE_BASE

# Install dependencies
RUN apt-get update -qq \
 && apt-get install -qq -y sudo time 2>&1 | grep 'Setting up' \
 && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY --from='requirements' ./tests.txt /tmp/
RUN export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q -r /tmp/tests.txt --no-cache-dir --upgrade \
 && rm -f /tmp/tests.txt
