import tarfile

from ..utils import read_json, blob_path, digest_bytes
from ..tags import OCI_LAYOUT_VERSION


class TarTree:
    """Read OCI layout files from a tar without extracting untrusted paths."""

    def __init__(self, filename):
        self.filename = filename
        self.tar = tarfile.open(filename, "r:*")
        self.members = {
            m.name.rstrip("/"): m
            for m in self.tar.getmembers()
            if m.isfile()
        }

        # Find index.json, supporting archives with a wrapping directory.
        candidates = [
            name for name in self.members
            if name == "index.json" or name.endswith("/index.json")
        ]

        candidates = [
            name for name in candidates
            if (
                name.rsplit("/", 1)[0] + "/oci-layout"
                if "/" in name
                else "oci-layout"
            ) in self.members
        ]

        if len(candidates) != 1:
            self.close()
            raise ValueError(
                f"{filename}: expected one OCI layout index.json, "
                f"found {len(candidates)}: {candidates}"
            )

        self.index_name = candidates[0]
        self.prefix = self.index_name[:-len("index.json")]
        layout_name = self.prefix + "oci-layout"

        if layout_name not in self.members:
            self.close()
            raise ValueError(f"{filename}: missing oci-layout")

        layout = read_json(self.read_member(layout_name), layout_name)
        if layout.get("imageLayoutVersion") != OCI_LAYOUT_VERSION:
            self.close()
            raise ValueError(f"{filename}: unsupported OCI layout version")

        self.index = read_json(
            self.read_member(self.index_name), self.index_name
        )
        if not isinstance(self.index.get("manifests"), list):
            self.close()
            raise ValueError(f"{filename}: index.json has no manifests array")

    def read_member(self, name):
        member = self.members.get(name)
        if member is None:
            raise ValueError(f"{self.filename}: missing {name}")
        stream = self.tar.extractfile(member)
        if stream is None:
            raise ValueError(f"{self.filename}: cannot read {name}")
        return stream.read()

    def read_blob(self, digest):
        name = self.prefix + blob_path(digest).as_posix()
        data = self.read_member(name)
        actual = digest_bytes(data)
        if actual != digest:
            raise ValueError(
                f"{self.filename}: digest mismatch for {name}: {actual}"
            )
        return data

    def close(self):
        self.tar.close()
