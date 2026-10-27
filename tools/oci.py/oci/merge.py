#!/usr/bin/env python3
"""Merge OCI layout tar archives and tag each manifest."""

import sys
from argparse import ArgumentParser, Namespace as ArgsNS
from tarfile import TarError
from .tags import (
    OCI_MEDIATYPE_INDEX,
    DOCKER_REF_TYPE,
    DOCKER_REF_DIGEST
)
from .layout.merge import MergeTree
from .layout.tar import TarTree
from .utils import read_json, platform_name


def resolve_manifests(source, descriptors):
    """Resolve top-level descriptors that point to nested OCI indexes."""
    resolved = []

    for descriptor in descriptors:
        media_type = descriptor.get("mediaType", "")

        if media_type == OCI_MEDIATYPE_INDEX:
            data = source.read_blob(descriptor["digest"])
            nested = read_json(data, descriptor["digest"])
            resolved.extend(resolve_manifests(
                source, nested.get("manifests", [])))
        else:
            resolved.append(descriptor)

    return resolved


def merge(inputs, output, tag_prefixes=None):
    sources = []
    mergetree = MergeTree(output)

    try:
        for filename in inputs:
            sources.append(TarTree(filename))

        for input_number, source in enumerate(sources):
            prefix = tag_prefixes[input_number] if tag_prefixes else ""

            # Resolve top-level indexes to their actual manifest descriptors.
            descriptors = resolve_manifests(
                source, source.index["manifests"]
            )

            # Keep the image manifest and attestation only.
            attestations = [
                d for d in descriptors
                if (
                    d.get("platform", {}).get("os") == "unknown"
                    and d.get("platform", {}).get("architecture") == "unknown"
                    and d.get("annotations", {}).get(DOCKER_REF_TYPE) == "attestation-manifest"
                )
            ]

            if len(attestations) != 1:
                raise ValueError(
                    f"{source.filename}: expected one attestation; "
                    f"found {len(attestations)}"
                )

            attestation = attestations[0]
            image_digest = attestation.get(
                "annotations", {}).get(DOCKER_REF_DIGEST)

            images = [
                d for d in descriptors
                if d.get("digest") == image_digest
            ]

            if len(images) != 1:
                raise ValueError(
                    f"{source.filename}: expected one image manifest for "
                    f"{image_digest}; found {len(images)}"
                )

            image = images[0]
            platform = platform_name(image)

            if not platform:
                raise ValueError(
                    f"{source.filename}: image manifest has no known platform"
                )

            # Copy only the leaf manifest trees and their referenced blobs.
            mergetree.copy_descriptor_tree(source, image)
            mergetree.copy_descriptor_tree(source, attestation)

            # The output index contains these two manifest descriptors only.
            image_tag = prefix + platform
            attestation_tag = prefix + platform + "-attestation"

            mergetree.add_tag(image_tag, image, source.filename, "latest")
            mergetree.add_tag(attestation_tag, attestation,
                              source.filename, "attestation")

        mergetree.finish()
    finally:
        for source in sources:
            source.close()


def build_parser(parser: ArgumentParser):
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output OCI layout directory",
    )
    parser.add_argument(
        "--tag-prefix",
        action="append",
        default=None,
        help="Optional per-input tag prefix; specify once per input",
    )
    parser.add_argument(
        "archives",
        nargs="+",
        help="OCI image-layout tar archives",
    )


def validate_args(parser: ArgumentParser, args: ArgsNS) -> None:
    if args.tag_prefix and len(args.tag_prefix) != len(args.archives):
        parser.error("--tag-prefix must be supplied once per input archive")


def run(args: ArgsNS):

    try:
        merge(args.archives, args.output, args.tag_prefix)
    except (ValueError, OSError, TarError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

# vim: ts=4:et:
