ARG builder=docker.io/alpine:edge

FROM ${builder} AS builder
RUN apk add gcc musl-dev make linux-headers
WORKDIR /builder
COPY --parents=true src arch include Makefile /builder

ARG TARGETVARIANT
RUN make -j$(nproc) VARIANT='$(TARGETVARIANT)' archdirs=no

FROM scratch
COPY --from=builder /builder/build/unemployd.stripped /unemployd
ENTRYPOINT ["/unemployd"]
