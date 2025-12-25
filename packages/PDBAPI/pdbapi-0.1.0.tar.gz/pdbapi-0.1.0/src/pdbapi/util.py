from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path

import pylinks

if TYPE_CHECKING:
    from pdbapi.typing import FileContentLike, PathLike


def write_to_file(
    content: FileContentLike,
    filename: str,
    extension: str | None = None,
    path: PathLike | None = None
) -> Path:
    if path is None:
        dir_path = Path.cwd()
    else:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
    fullpath = (dir_path / filename).resolve()
    if extension is not None:
        ext = f".{extension.removeprefix(".")}" if extension else ""
        fullpath = fullpath.with_suffix(ext)
    mode = "xb" if isinstance(content, bytes) else "xt"
    with open(fullpath, mode) as f:
        f.write(content)
    return fullpath


def http_request(url: str, response_type: str = "json") -> dict:
    """
    Send data query and get results in dict format.

    Parameters
    ----------
    url : str
        Full URL of the API query.

    Returns
    -------
    dict
    """
    return pylinks.http.request(url=url, response_type=response_type)
