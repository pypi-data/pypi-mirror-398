# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

"""Utilities for building stable checkpoint keys.

This module centralizes the hashing and formatting logic so both UDFs and
map tasks can compose checkpoint keys consistently.
"""

import hashlib


def hash_string(value: str | None) -> str:
    """Return a stable md5 hex digest for the given string (or empty).

    The empty string is used for ``None`` values so that the hash is
    deterministic and safe for filesystem paths.
    """

    hasher = hashlib.md5()
    hasher.update((value or "").encode())
    return hasher.hexdigest()


def format_checkpoint_prefix(
    *,
    udf_name: str,
    udf_version: str,
    column: str,
    where: str | None,
    dataset_uri: str,
    dataset_version: int | str | None,
) -> str:
    """Compose the prefix portion of a checkpoint key.

    The returned string follows the convention:
    ``udf-{name}_ver-{version}_col-{column}_where-{hash(where)}_uri-{hash(uri)}_ver-{dataset_version}``
    """

    version_part = "latest" if dataset_version is None else str(dataset_version)
    return (
        f"udf-{udf_name}_ver-{udf_version}"
        f"_col-{column}_where-{hash_string(where)}"
        f"_uri-{hash_string(dataset_uri)}_ver-{version_part}"
    )


def format_checkpoint_key(prefix: str, *, frag_id: int, start: int, end: int) -> str:
    """Attach fragment and range information to a checkpoint prefix."""

    return f"{prefix}_frag-{frag_id}_range-{start}-{end}"
