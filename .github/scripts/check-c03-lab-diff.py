"""Compare the immutable Git objects without executing PR code."""

import json
import re
import subprocess
import sys

VALUES = "ai-ops/lab/values.yaml"
REPOSITORY = "764428911194.dkr.ecr.ap-northeast-2.amazonaws.com/urlshortener"


def git(*args):
    return subprocess.check_output(["git", *args], timeout=10)


def digest(revision):
    entry = git("ls-tree", revision, "--", VALUES)
    if not re.fullmatch(rb"100644 blob [a-f0-9]{40}\tai-ops/lab/values.yaml\n", entry):
        raise ValueError("unexpected values entry")
    data = git("show", f"{revision}:{VALUES}")
    image_digest = json.loads(data)["api"]["image"]["digest"]
    canonical = {"api": {"image": {"repository": REPOSITORY, "digest": image_digest}}}
    if (not re.fullmatch(r"sha256:[a-f0-9]{64}", image_digest)
            or data != (json.dumps(canonical, indent=2) + "\n").encode()):
        raise ValueError("unexpected values content")
    return image_digest


def main(base, head):
    if not all(re.fullmatch(r"[a-f0-9]{40}", sha) for sha in (base, head)):
        raise ValueError("invalid commit SHA")
    if git("rev-list", "--parents", "-n", "1", head).decode().split() != [head, base]:
        raise ValueError("proposal must be a single commit on the current base")
    if git("diff", "--name-status", "-z", base, head) != b"M\0" + VALUES.encode() + b"\0":
        raise ValueError("proposal must modify only the lab values file")
    if digest(base) == digest(head):
        raise ValueError("proposal does not change the digest")


if __name__ == "__main__":
    main(*sys.argv[1:])
