FROM oef-search:latest_builder AS builder

RUN ls | grep -v '^bazel-' | grep -v 'fetch_teams' | xargs rm -rf && \
    cd fetch_teams && ls | grep -v '^oef-core' | xargs rm -rf && \
    cd oef-core && ls | grep -v '^build' | xargs rm -rf

ADD project.tar.gz /app

WORKDIR /app/project

RUN rm -f .bazelrc && \
    cd fetch_teams/oef-core && mkdir build -p && cd build && cmake .. && make -j16 && cd /app/project && \
    bazel build network_oef/experimental/python:node --force_python=PY3 && \
    bazel build network_oef/experimental/python/demo:demo_director --force_python=PY3 && \
    cp certificates/src/makefiles/oef-search/oef-search.pem /build/server.pem  && \
    cp -Lr bazel-bin /build && \
    cp network_oef/experimental/sh/oef.sh /build/

FROM qati/oef-search:runtime AS runtime

WORKDIR /app

COPY gensim-data /root/gensim-data
COPY nltk_data /root/nltk-data
COPY --from=builder /build/bazel-bin/network_oef/experimental/python /app/
COPY --from=builder /build/server.pem /app/
COPY --from=builder /build/oef.sh /app/
COPY --from=builder /app/project/cpp-sdk/experimental/resources /app/cpp-sdk/experimental/resources
COPY --from=builder /app/project/ai_search_engine/src/resources/ /app/ai_search_engine/src/resources

RUN apk add protobuf && \
    apk add tcpdump && \
    apk add iproute2 && \
    pip3 install colorlog && \
    chmod +x /app/oef.sh

ENTRYPOINT ["/bin/sh", "/app/oef.sh"]