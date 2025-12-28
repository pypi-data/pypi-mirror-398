import io
import json
import logging
import tarfile
import time
from typing import Any, Dict

import cloudpickle
import numpy as np
import zstandard as zstd  # type: ignore

logger = logging.getLogger("neuralk_nicl_client")


def _add_file(archive, writer, name):
    buffer = io.BytesIO()
    writer(buffer)
    buffer.seek(0)
    info = tarfile.TarInfo(name=name)
    info.size = len(buffer.getvalue())
    archive.addfile(info, buffer)


def _add_json(archive, data, stem):
    _add_file(
        archive, lambda f: f.write(json.dumps(data).encode("utf-8")), f"{stem}.json"
    )


def _add_array(archive, data, stem):
    _add_file(archive, lambda f: np.save(f, data), f"{stem}.npy")


def create_tar(
    metadata: Dict[str, Any] | None = None,
    arrays: Dict[str, np.ndarray] | None = None,
    raw_data: Dict[str, bytes] | None = None,
) -> io.BytesIO:
    """
    Build a tar archive containing:
      - metadata.json (augmented with {"version": 1} if missing)
      - *.npy arrays
      - arbitrary raw files
    Then compress with zstd.
    Returns a BytesIO positioned at start.
    """
    meta = dict(metadata or {})
    meta.setdefault("version", 1)

    uncompressed = io.BytesIO()
    # Write an uncompressed tar (so we can choose compressor)
    with tarfile.open(fileobj=uncompressed, mode="w") as archive:
        _add_json(archive, meta, "metadata")
        for name, a in (arrays or {}).items():
            _add_array(archive, a, name)
        for name, d in (raw_data or {}).items():
            _add_file(archive, lambda f: f.write(d), name)
    uncompressed.seek(0)

    # Compress with zstd
    cctx = zstd.ZstdCompressor(level=6)
    out = io.BytesIO()
    with cctx.stream_writer(out, closefd=False) as zw:
        zw.write(uncompressed.read())
    out.seek(0)
    return out


def _stem(name):
    return name.rsplit(".", 1)[0]


def extract_tar(file, load_cloudpickle=False):
    result = {}
    # Support zstd-compressed tar streams (client default) transparently
    start = file.read(4)
    file.seek(0)
    # zstd magic = 0x28B52FFD
    if start == b"\x28\xb5\x2f\xfd" and zstd is not None:
        dctx = zstd.ZstdDecompressor()
        decompressed = io.BytesIO(dctx.decompress(file.read()))
        archive = tarfile.open(fileobj=decompressed, mode="r")
    else:
        archive = tarfile.open(fileobj=file, mode="r")
    with archive:
        for member in archive:
            member_file = archive.extractfile(member)
            if member.name.endswith(".npy"):
                result[_stem(member.name)] = np.load(
                    io.BytesIO(member_file.read()), allow_pickle=False
                )
            elif member.name.endswith(".json"):
                result[_stem(member.name)] = json.loads(
                    member_file.read().decode("utf-8")
                )
            elif member.name.endswith(".cloudpickle") and load_cloudpickle:
                result[_stem(member.name)] = cloudpickle.load(member_file)
            else:
                result[member.name] = member_file.read()
    return result


def health_check(url, headers, timeout=120, interval=2):
    """
    Wait until the health endpoint responds with HTTP 200.
    """
    end_time = time.time() + timeout
    attempt = 0
    while time.time() < end_time:
        attempt += 1
        try:
            import httpx  # type: ignore

            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{url}/health", headers=headers)
            if resp.status_code == 200 and resp.text.strip() == "OK":
                logger.info("Health check OK at %s", url)
                return True
        except Exception:
            pass

        logger.debug("Waiting for server health... attempt %d", attempt)
        time.sleep(interval)
    raise TimeoutError(f"Server did not respond on {url} within {timeout} seconds")
