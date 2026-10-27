import shutil
import time
from copy import deepcopy
from pathlib import Path
from ..cli import stderr, stdout, Tag as ANSITag
from ..tags import (
    OCI_MEDIATYPE_INDEX,
    OCI_REF_NAME,
    OCI_LAYOUT_VERSION,
    OCI_MEDIATYPE_BINARY,
)
from ..utils import (
    json_str, read_json, blob_path,
    safe_tag, digest_bytes,
    format_duration, format_size
)


class MergeTree:
    def __init__(self, output):
        self.output = Path(output)
        self.blobs = self.output / "blobs" / "sha256"
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.index_path = self.output / "index.json"
        self.layout_path = self.output / "oci-layout"
        self.tags = {}
        self.blob_count = 0

        if self.layout_path.exists():
            layout = read_json(
                self.layout_path.read_bytes(), str(self.layout_path)
            )
            if layout.get("imageLayoutVersion") != OCI_LAYOUT_VERSION:
                raise ValueError("Unsupported existing OCI layout version")
        else:
            self.layout_path.write_text(
                f"{json_str({'imageLayoutVersion': OCI_LAYOUT_VERSION})}\n")

        if self.index_path.exists():
            self.index = read_json(
                self.index_path.read_bytes(), str(self.index_path)
            )
            if self.index.get("schemaVersion") != 2:
                raise ValueError(
                    "Existing index has unsupported schemaVersion")
            if not isinstance(self.index.get("manifests"), list):
                raise ValueError("Existing index has no manifests array")
        else:
            self.index = {
                "schemaVersion": 2,
                "mediaType": OCI_MEDIATYPE_INDEX,
                "manifests": [],
            }

        # Validate and register existing tags.
        for desc in self.index["manifests"]:
            self.validate_descriptor(desc)
            tag = desc.get("annotations", {}).get(OCI_REF_NAME)
            if tag:
                if tag in self.tags:
                    raise ValueError(f"Duplicate existing tag: {tag}")
                self.tags[tag] = desc

    @staticmethod
    def validate_descriptor(desc):
        if not isinstance(desc, dict):
            raise ValueError("Manifest descriptor must be an object")

        digest = desc.get("digest")
        size = desc.get("size")
        media_type = desc.get("mediaType")

        if not isinstance(digest, str):
            raise ValueError("Descriptor is missing digest")
        blob_path(digest)

        if not isinstance(size, int) or size < 0:
            raise ValueError(f"Invalid descriptor size for {digest}")
        if not isinstance(media_type, str) or not media_type:
            raise ValueError(f"Missing mediaType for {digest}")

    def copy_blob_data(
        self, digest, data, expected_size=None, media_type=None
    ):
        started = time.perf_counter()

        if digest_bytes(data) != digest:
            raise ValueError(f"Digest mismatch for {digest}")

        if expected_size is not None and len(data) != expected_size:
            raise ValueError(
                f"Size mismatch for {digest}: expected {expected_size}, "
                f"got {len(data)}"
            )

        _, _, value = digest.partition(":")
        target = self.blobs / value

        if target.exists():
            existing = target.read_bytes()

            if digest_bytes(existing) != digest:
                raise ValueError(f"Corrupt existing output blob: {target}")

            if len(existing) != len(data):
                raise ValueError(f"Existing blob size mismatch: {target}")

            action = "Exists"
        else:
            target.write_bytes(data)
            self.blob_count += 1
            action = "Copied"

        elapsed = time.perf_counter() - started

        self.progress_status(
            action,
            media_type or OCI_MEDIATYPE_BINARY,
            len(data),
            elapsed,
            digest,
        )

    def copy_blob(self, source, descriptor):
        digest = descriptor["digest"]
        data = source.read_blob(digest)

        self.copy_blob_data(
            digest,
            data,
            descriptor.get("size"),
            descriptor.get("mediaType"),
        )

    def has_valid_blob(self, descriptor):
        """Return True if the output already contains this valid blob."""
        digest = descriptor["digest"]
        _, _, value = digest.partition(":")
        target = self.blobs / value

        if not target.is_file():
            return False

        # Avoid rereading and hashing an existing blob on every invocation.
        if descriptor.get("size") is not None:
            if target.stat().st_size != descriptor["size"]:
                raise ValueError(f"Existing blob size mismatch: {target}")

        return True

    def copy_descriptor_tree(self, source, descriptor, seen=None):
        if seen is None:
            seen = set()

        digest = descriptor["digest"]
        if digest in seen:
            return
        seen.add(digest)

        # A completed manifest means its entire tree was copied.
        if self.has_valid_blob(descriptor):
            digest = descriptor["digest"]
            _, _, value = digest.partition(":")
            target = self.blobs / value

            self.progress_status(
                "Exists",
                descriptor.get("mediaType", OCI_MEDIATYPE_BINARY),
                target.stat().st_size,
                0,
                digest,
            )
            return

        data = source.read_blob(digest)

        media_type = descriptor.get("mediaType", "")
        is_manifest = "manifest" in media_type or "index" in media_type

        if is_manifest:
            document = read_json(data, digest)

            config = document.get("config")
            if config:
                self.copy_blob(source, config)

            for layer in document.get("layers", []):
                self.copy_blob(source, layer)

            for child in document.get("manifests", []):
                self.copy_descriptor_tree(source, child, seen)

        # Commit this manifest only after all referenced blobs are copied.
        self.copy_blob_data(
            digest,
            data,
            descriptor.get("size"),
            media_type,
        )

    def add_tag(self, tag, descriptor, source, source_tag):
        tag = safe_tag(tag)
        self.validate_descriptor(descriptor)

        existing = self.tags.get(tag)

        tagged = deepcopy(descriptor)
        annotations = dict(tagged.get("annotations", {}))
        annotations[OCI_REF_NAME] = tag
        tagged["annotations"] = annotations

        if existing:
            position = self.index["manifests"].index(existing)
            self.index["manifests"][position] = tagged
        else:
            self.index["manifests"].append(tagged)

        self.tags[tag] = tagged

        self.tag_status(source, source_tag, tag, descriptor['digest'])

    def finish(self):
        # Validate every entry and every tag before committing.
        seen_tags = set()
        seen_descriptors = set()

        for desc in self.index["manifests"]:
            self.validate_descriptor(desc)
            tag = desc.get("annotations", {}).get(OCI_REF_NAME)

            if tag:
                if tag in seen_tags:
                    raise ValueError(f"Duplicate tag in output: {tag}")
                seen_tags.add(tag)

            identity = (desc["digest"], tag)
            if identity in seen_descriptors:
                raise ValueError(f"Duplicate index entry: {identity}")
            seen_descriptors.add(identity)

            _, _, value = desc["digest"].partition(":")
            blob = self.blobs / value
            if not blob.is_file():
                raise ValueError(f"Missing manifest blob: {desc['digest']}")

            data = blob.read_bytes()
            if digest_bytes(data) != desc["digest"]:
                raise ValueError(f"Corrupt manifest blob: {desc['digest']}")
            if len(data) != desc["size"]:
                raise ValueError(f"Manifest size mismatch: {desc['digest']}")

        self.index["mediaType"] = OCI_MEDIATYPE_INDEX
        payload = json_str(self.index).encode("utf-8") + b"\n"

        # Atomic replacement prevents a partial index on interruption.
        temporary = self.index_path.with_suffix(".json.tmp")
        temporary.write_bytes(payload)
        temporary.replace(self.index_path)

    def tag_status(self, source, source_tag, output_tag, digest):
        print(
            f"%F[green]Copied%f [oci-layout] "
            f"{source}:{source_tag} => [oci-layout] {self.output.name}:{output_tag}",
            file=stderr,
            flush=True,
        )
        print(f"Digest: {digest}", file=stdout, flush=True)

    @staticmethod
    def progress_status(action, media_type, size_b, elapsed, digest):
        terminal_width = shutil.get_terminal_size(fallback=(100, 24)).columns

        size, unit = format_size(size_b)
        duration = format_duration(elapsed)
        color = "green" if action == "Copied" else "cyan"

        prefix = f"%F[green]✓ %F[{color}]{action:<6}%f  "
        suffix = f" 100.00% {duration:>6}"

        # Reserve room for the size, percentage, duration, and separators.
        suffix_width = len(f"{size}/{size} {unit:>2}{suffix}")
        media_width = max(
            10, terminal_width - len(ANSITag.format(prefix, tty=False)) - suffix_width - 2)

        if len(media_type) > media_width:
            media_type = media_type[:media_width - 1] + "…"

        line = (
            f"{prefix}{media_type:<{media_width}}  "
            f"{size}/{size} {unit:>2}{suffix}\n"
            f"  └─ {digest}"
        )

        print(line, file=stderr, flush=True)
