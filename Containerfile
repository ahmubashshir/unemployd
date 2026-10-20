FROM docker.io/alpine:latest AS builder
RUN apk add gcc musl-dev make linux-headers
WORKDIR /src
COPY --parents=true *.c *.h arch/* LSS/*.h discard.ld Makefile /src

RUN make -j$(nproc)

FROM scratch
COPY --from=builder /src/unemployd.stripped /unemployd
ENTRYPOINT ["/unemployd"]
