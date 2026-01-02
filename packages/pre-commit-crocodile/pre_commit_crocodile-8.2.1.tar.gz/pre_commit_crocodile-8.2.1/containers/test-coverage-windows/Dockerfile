ARG IMAGE_BASE=tobix/pywine:latest
FROM $IMAGE_BASE

# Install dependencies
RUN echo 'wine pip3 "${@}"' | tee /usr/local/bin/pip3 >/dev/null \
 && chmod a+x /usr/local/bin/pip3 \
 && export PIP_DISABLE_PIP_VERSION_CHECK=1 \
 && pip3 install -q --no-cache-dir --upgrade wheel 2>/dev/null

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
 && rm -f /tmp/tests.txt \
 && echo 'wine coverage "${@}"' | tee /usr/local/bin/coverage >/dev/null \
 && chmod a+x /usr/local/bin/coverage
