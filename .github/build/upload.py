"""Upload build artifacts to the server in GitHub Actions.

This script scans the ``core`` directory, uploads files using the server's upload endpoint,
and then triggers a restart endpoint. It prefers pathlib, explicit typing, and robust async handling.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

import aiohttp


def sign(key: str) -> dict[str, str]:
    """Generate request signature headers.

    Returns a mapping with "signature" and "timestamp" fields.
    """
    # Use integer seconds to match original server expectation
    import time

    ts = str(int(time.time()))
    signature = hashlib.sha256(f"{key}AS{ts}".encode()).hexdigest()
    return {"signature": signature, "timestamp": ts}


@dataclass(slots=True)
class UploadResult:
    ok: bool
    status: int
    detail: str | None = None


async def upload(
    session: aiohttp.ClientSession,
    server: str,
    key: str,
    path: str,
    file_bytes: bytes,
) -> UploadResult:
    """Upload a single file.

    Expects the server to accept PUT with params: path, site and JSON body response with a "code".
    """
    try:
        async with session.put(
            server,
            headers=sign(key),
            params={"path": path, "site": "back"},
            data={"file": file_bytes},
        ) as r:
            status = r.status
            # Try parse JSON; server response is expected to be JSON with a code
            try:
                payload = await r.json(content_type=None)
            except Exception:  # noqa: BLE001 - tolerate non-JSON error bodies
                text = await r.text()
                return UploadResult(ok=False, status=status, detail=text[:500])

            code = payload.get("code")
            if isinstance(code, int) and code == 200:
                return UploadResult(ok=True, status=status)
            return UploadResult(ok=False, status=status, detail=str(code))
    except aiohttp.ClientError as e:
        return UploadResult(ok=False, status=0, detail=str(e))


def iter_files(root: Path) -> Iterable[tuple[Path, str]]:
    """Yield (absolute_file_path, posix_relative_path_from_root)."""
    for p in root.rglob("*"):
        if p.is_file():
            yield p, p.relative_to(root).as_posix()


def get_restart_url(server: str) -> str:
    return server + "restart" if server.endswith("/") else server + "/restart"


async def main() -> None:
    server = os.environ.get("SERVER")
    key = os.environ.get("KEY")

    if not server:
        raise RuntimeError("Environment variable SERVER is required")
    if not key:
        raise RuntimeError("Environment variable KEY is required")

    root = Path.cwd() / "core"
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    files = list(iter_files(root))
    total = len(files)

    async with aiohttp.ClientSession() as session:
        for idx, (abs_path, rel_path) in enumerate(files, start=1):
            res = await upload(session, server, key, rel_path, abs_path.read_bytes())
            if res.ok:
                print(f"[{idx}/{total}] upload {rel_path} successfully")
            else:
                print(f"[{idx}/{total}] upload {rel_path} failed\nstatus={res.status} detail={res.detail}")

        # Trigger restart
        restart_url = get_restart_url(server)
        try:
            async with session.post(restart_url, headers=sign(key)) as r:
                try:
                    resp = await r.json(content_type=None)
                except Exception as exc:  # noqa: BLE001
                    text = await r.text()
                    raise RuntimeError(f"restart failed: HTTP {r.status} body={text[:500]}") from exc

                if resp.get("code") == 200:
                    print("restart server")
                else:
                    raise RuntimeError(f"restart failed: {resp}")
        except aiohttp.ClientError as e:
            raise RuntimeError(f"restart request error: {e}") from e


if __name__ == "__main__":
    asyncio.run(main())
