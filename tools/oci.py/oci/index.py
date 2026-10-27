#!/usr/bin/env python3
"""Create an OCI image index for given tags."""

import hashlib
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from argparse import (
    ArgumentParser,
    ArgumentTypeError,
    Namespace as ArgsNS,
)

from .tags import (
    OCI_MEDIATYPE_INDEX,
    OCI_LAYOUT_VERSION,
    OCI_REF_NAME
)

from .utils import json_str, read_json, blob_path


def write_json_atomic(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".index-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"{json_str(obj)}\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def resolve_descriptor(layout_index, source):
    """Resolve a tag or digest to its original descriptor."""
    manifests = layout_index.get("manifests", [])

    matches = [
        d for d in manifests
        if d.get("digest") == source
        or d.get("annotations", {}).get(
            OCI_REF_NAME
        ) == source
    ]

    if len(matches) != 1:
        raise ValueError(
            f"{source!r}: expected one matching descriptor, "
            f"found {len(matches)}"
        )

    # Copy the entire descriptor, not a reconstructed subset.
    return deepcopy(matches[0])


def read_verified_manifest(layout, descriptor):
    path = blob_path(descriptor["digest"], layout)
    raw = path.read_bytes()

    actual_digest = (
        descriptor["digest"].split(":", 1)[0]
        + ":"
        + hashlib.new(
            descriptor["digest"].split(":", 1)[0], raw
        ).hexdigest()
    )

    if actual_digest != descriptor["digest"]:
        raise ValueError(f"Digest mismatch: {path}")

    if len(raw) != descriptor["size"]:
        raise ValueError(f"Size mismatch: {path}")

    return raw, read_json(raw)


def log(action, message):
    print(f"{action:<10}{message}", flush=True)


def parse_tags(value: str) -> list[str]:
    tags = value.split(",")
    if any(not tag.strip() for tag in tags):
        raise ArgumentTypeError(
            "must contain non-empty comma-separated tags"
        )

    if any(tag != tag.strip() for tag in tags):
        raise ArgumentTypeError(
            "tags must not contain surrounding whitespace"
        )

    tags = [tag.strip() for tag in tags]
    if not all(tags):
        raise ArgumentTypeError("must contain at least one tag")

    return tags


def parse_annotation(item: str) -> tuple[str, str]:
    key, sep, value = item.partition("=")
    if not sep or not key:
        raise ArgumentTypeError(f"invalid annotation: {item!r}")
    return key, value


def build_parser(parser: ArgumentParser):
    parser.add_argument("layout", help="OCI layout directory")
    parser.add_argument(
        "--tag", required=True,
        type=parse_tags,
        help="Comma-separated output tags, e.g. v1,latest",
    )
    parser.add_argument(
        "sources", nargs="+",
        help="Existing source tags or sha256 digests in the layout",
    )
    parser.add_argument(
        "--annotation", action="append", default=[],
        type=parse_annotation,
        metavar="KEY=VALUE",
        help="Index-level annotation (repeatable)",
    )
    parser.add_argument(
        "--artifact-type",
        help="Optional OCI index artifactType",
    )


def run(args: ArgsNS):
    layout = Path(args.layout)
    layout_index_path = layout / "index.json"
    layout_meta_path = layout / "oci-layout"

    if not layout_meta_path.exists():
        raise FileNotFoundError(f"Not an OCI layout: {layout}")

    layout_index = read_json(layout_index_path, file=True)
    layout_meta = read_json(layout_meta_path, file=True)

    if layout_meta.get("imageLayoutVersion") != OCI_LAYOUT_VERSION:
        raise ValueError("Unsupported OCI layout version")

    # Preserve all source descriptors, including unknown platforms,
    # annotations, URLs, embedded data, and extension properties.
    descriptors = []
    for source in args.sources:
        log("Fetching", source)

        descriptor = resolve_descriptor(layout_index, source)
        read_verified_manifest(layout, descriptor)
        descriptors.append(descriptor)

        platform = descriptor.get("platform", {})
        log("Fetched", f"{descriptor['digest']}")
    # Preserve the original bytes and verify every referenced manifest.
    for descriptor in descriptors:
        annotations = descriptor.get("annotations", {})
        annotations.pop(OCI_REF_NAME, None)

        if not annotations:
            descriptor.pop("annotations", None)

        read_verified_manifest(layout, descriptor)

    index = {
        "schemaVersion": 2,
        "mediaType": OCI_MEDIATYPE_INDEX,
        "manifests": descriptors,
    }

    if args.artifact_type:
        index["artifactType"] = args.artifact_type

    annotations = dict(args.annotation)
    if annotations:
        index["annotations"] = annotations

    # The index itself is content-addressed.
    raw = json_str(index).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    size = len(raw)
    blob = blob_path(digest, layout)
    blob.parent.mkdir(parents=True, exist_ok=True)

    if blob.exists() and blob.read_bytes() != raw:
        raise ValueError(f"Unexpected existing blob: {blob}")

    if not blob.exists():
        fd, tmp = tempfile.mkstemp(dir=blob.parent, prefix=".blob-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, blob)
        except BaseException:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
            raise
    log("Packed", f"{digest[7:20]} {OCI_MEDIATYPE_INDEX}")

    # Keep unrelated layout entries and their metadata intact.
    root = deepcopy(layout_index)
    root.setdefault("schemaVersion", 2)
    root_manifests = root.setdefault("manifests", [])

    # Remove ALL existing root-level tag references.
    # The copied manifests remain in the newly created index blob.
    root_manifests.clear()

    for tag in args.tag:
        # Replace only this tag's root reference.
        root_manifests.append({
            "mediaType": OCI_MEDIATYPE_INDEX,
            "digest": digest,
            "size": size,
            "annotations": {
                OCI_REF_NAME: tag
            },
        })

    write_json_atomic(layout_index_path, root)
    log("Pushed", f"[oci-layout] {str(layout)}:{args.tag[0]}")
    for tag in args.tag[1:]:
        log("Tagged", tag)
    print(f"Digest: {digest}")

# vim: ts=4:et:
