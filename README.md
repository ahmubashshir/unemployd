## unemployd

This is probably the least productive container you'll ever run.

It's for those times when your Docker Compose stack or
Kubernetes deployment needs a container that doesn't actually need to do anything.

It does absolutely nothing, just to keep your container orchestrator happy.
It even waits for `SIGINT` or `SIGTERM` before leaving, because apparently,
doing nothing isn't enough; it has to do nothing responsibly.

## Usage
```sh
podman run --rm -d ahmubashshir/unemployd:latest
```

Replace podman with docker if that's your thing.

See [example.yaml](example.yaml) for Kubernetes or Compose.

<!-- build:start -->
## Building
```sh
podman build -t unemployd .
```

Or use Docker. Whatever keeps you employed.

Or install gcc, then run `make`.
<!-- build:end -->

## FAQs
 * Q: Why does this exist?<br />
   A: The orchestrator wanted a container. Who am I to argue?
 * Q: What does it do?<br />
   A: Absolutely nothing. Please don't distract it.
 * Q: Only Docker Hub?<br />
   A: Nope! GHCR[^1] too.
 * Q: Should I use it?<br />
   A: If you need a container that does nothing, you've come to the right place.
 * Q: What architecture does this support?<br />
   A: Whatever `alpine:edge` supports. We're not picky.
 * Q: Why not just use `sleep infinity`?<br />
   A: You dare want a proper rootfs just to sleep on it?
 * Q: Does it consume resources?<br />
   A: It consumes a PID, some memory, and less than one AF[^2] sector.
 * Q: Why is it called unemployd?<br />
   A: It got the job. It just doesn't do the job.
 * Q: Does it support graceful shutdown?<br />
   A: Of course. Even unemployed daemons have to know when to leave.
 * Q: Is this production-ready?<br />
   A: It's production-nothing.
 * Q: Why did you create it?<br />
   A: I had nothing better to do.

## License

See [LICENSE](LICENSE).

[^1]: `ghcr.io/ahmubashshir/unemployd:latest`
[^2]: [Advanced Format (4Kn)](https://en.wikipedia.org/wiki/Advanced_Format#4K_native_(4Kn))
