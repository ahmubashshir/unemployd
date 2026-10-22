FROM docker.io/alpine:latest AS builder
RUN apk add gcc musl-dev make linux-headers
WORKDIR /build
COPY --parents=true src arch include Makefile /build

ARG TARGETVARIANT
RUN make -j$(nproc) VARIANT='$(TARGETVARIANT)'

FROM scratch
COPY --from=builder /build/src/unemployd.stripped /unemployd
ENTRYPOINT ["/unemployd"]
