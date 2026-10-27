import re
from hashlib import sha256
from json import (
    dumps as json_dump,
    loads as json_load,
    JSONDecodeError,
)
from pathlib import Path


def json_str(obj):
    return json_dump(obj, sort_keys=False, separators=(",", ":"))


def read_json(source, description=None, *, file=False):
    """Read JSON from a file or parse JSON content."""
    try:
        if file:
            with open(source, "rb") as f:
                return json_load(f.read())
        return json_load(source)
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(
            f"Invalid JSON in {description or source}: {exc}"
        ) from exc


def blob_path(digest, layout=None):
    algorithm, sep, encoded = digest.partition(":")

    if not sep or not algorithm or not encoded:
        raise ValueError(f"Invalid digest: {digest}")

    if algorithm != "sha256":
        raise ValueError(f"Unsupported digest: {digest}")

    if not re.fullmatch(r"[0-9a-f]{64}", encoded):
        raise ValueError(f"Invalid SHA-256 digest: {digest}")

    path = Path("blobs") / algorithm / encoded
    return Path(layout) / path if layout is not None else path


def safe_tag(value):
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value)
    value = value.strip(".-")
    if not value or not re.match(r"^[a-zA-Z0-9_]", value):
        value = "oci-" + value
    return value


def digest_bytes(data):
    return "sha256:" + sha256(data).hexdigest()


def platform_name(descriptor):
    platform = descriptor.get("platform", {})
    os_name = platform.get("os")
    arch = platform.get("architecture")

    if os_name and arch and os_name != "unknown" and arch != "unknown":
        parts = [os_name, arch]
        if platform.get("variant"):
            parts.append(platform["variant"])
        return "-".join(parts)

    return None


def format_size(size):
    if size >= 1024:
        value = float(size)
        for unit in ("KB", "MB", "GB", "TB"):
            value /= 1024
            if value < 1024 or unit == "TB":
                return (f"{value:.2f}", unit)

    return (f'{size}', 'B')


def format_duration(seconds):
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f}µs"
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.0f}s"

# vim: ts=4:et:
