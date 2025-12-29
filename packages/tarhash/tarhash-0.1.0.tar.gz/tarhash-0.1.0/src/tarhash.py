from __future__ import annotations

import hashlib
import importlib
import re
import sys
import tarfile
from functools import cache
from tarfile import TarInfo
from typing import IO, TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from collections.abc import Iterator

import click


class UnsupportedDigestError(click.ClickException, ValueError):
    digest_name: str

    def __init__(self, name: str) -> None:
        super().__init__(f"Unknown or unsupported hash algorithm: {name!r}")


KNOWN_NONSTD_HASHES: dict[str, Optional[set[str]]] = {
    "blake3": {"blake3"},
    "xxhash": None,
}
NONSTD_HASH_ALIASES: dict[str, str] = {
    # xxh3 and xxh128 are semi-official shorthands
    "xxhash.xxh3_64": "xxh3",
    "xxhash.xxh3_128": "xxh128",
}
STD_HASH_ALIASES: dict[str, str] = {
    "blake2": "blake2b",  # This is the variant chosen by 'blake2b'
}


@cache
def nonstd_hashes() -> dict[str, Any]:
    result_hashes = {}

    for module_name, supported_hashes in KNOWN_NONSTD_HASHES.items():
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        if supported_hashes is None:
            supported_hashes = set(module.algorithms_available)

        def add_hash(hash_name: str, hash_func: Any) -> None:
            result_hashes[hash_name] = hash_func
            full_name = f"{module_name}.{hash_name}"
            if (aliased_name := NONSTD_HASH_ALIASES.get(full_name)) is not None:
                add_hash(aliased_name, hash_func)

        for hash_name in supported_hashes:
            hash_func = getattr(module, hash_name)
            if not callable(hash_func):
                raise TypeError(type(hash_func))
            add_hash(hash_name, hash_func)

    return result_hashes


def resolve_digest(name: str) -> Any:
    # We do some additional name resolution logic here,
    # both for the stdlib aliases (not handled by nonstd_hashes)
    # and things we don't want to show up in `--digest=print`
    if name in STD_HASH_ALIASES:
        resolved_name = STD_HASH_ALIASES[name]
    elif re.fullmatch(r"xxhash[\d_]+", name):
        # I prefer xxhash3 to xxh3, even though the latter is the 'official' name
        resolved_name = name.replace("xxhash", "xxh")
    else:
        resolved_name = name

    nonstd_hash_functions = nonstd_hashes()
    if resolved_name in nonstd_hash_functions:
        return nonstd_hash_functions[resolved_name]
    else:
        try:
            return hashlib.new(resolved_name)
        except ValueError:
            raise UnsupportedDigestError(name) from None


if not TYPE_CHECKING and hasattr("hashlib", "digest_file"):
    digest_file = hashlib.digest_file
else:

    def digest_file(fileobj: IO[bytes], digest: Any) -> Any:
        if callable(digest):
            digest = digest()
        while b := fileobj.read(1024 * 16):
            digest.update(b)
        return digest


def hash_entries(tar: tarfile.TarFile, *, digest: str) -> Iterator[tuple[TarInfo, str]]:
    resolve_digest(digest)  # check once to give error
    for entry in tar:
        fileobj = tar.extractfile(entry)
        if fileobj is None:
            continue
        checksum = digest_file(fileobj, resolve_digest(digest)).hexdigest()
        yield (entry, checksum)


@click.command()
@click.option("--digest", type=str, default="sha256")
@click.option("--file", "-f", type=click.Path())
@click.option("--check", is_flag=True)
def tarhash(digest: str, file: str | None, check: bool) -> None:  # noqa: FBT001
    if digest == "print":
        available_digests = [*hashlib.algorithms_available, *nonstd_hashes().keys(), *STD_HASH_ALIASES.keys()]
        available_digests.sort()
        print("Available Digests:", file=sys.stderr)
        for item in available_digests:
            print(item)
        return
    if check:
        raise NotImplementedError("The --check argument has not been initialized")
    if file is None:
        raise click.ClickException("A `--file` or `-f` argument is required")
    resolve_digest(digest)
    with tarfile.open(file) as tar:
        for entry, checksum in hash_entries(tar, digest=digest):
            print(checksum, entry.name)


if __name__ == "__main__":
    tarhash()
