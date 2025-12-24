import hashlib


def hasher(algo: str) -> "hashlib._Hash":
    algo_lower = algo.lower()
    if algo_lower == "md5":
        return md5_hasher()
    else:
        try:
            return hashlib.new(algo_lower)
        except ValueError as e:
            raise ValueError(f"Unknown or unsupported hash algorithm: {algo}") from e


def md5_hasher() -> "hashlib._Hash":
    try:
        return hashlib.md5()
    except ValueError:
        try:
            return hashlib.md5(usedforsecurity=False)  # type: ignore[call-arg]
        except TypeError as e:
            raise RuntimeError("MD5 unavailable in this environment") from e
