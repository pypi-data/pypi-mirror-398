__version__ = "0.2.1"


try:
    from ubpe_cython import UBPE, UBPEClassic  # type: ignore
except ImportError:
    _has_ubpe_cython = False
else:
    _has_ubpe_cython = True


try:
    if not _has_ubpe_cython:
        from ubpe_native import UBPE, UBPEClassic  # type: ignore
    else:
        raise ImportError()
except ImportError:
    _has_ubpe_native = False
else:
    _has_ubpe_native = True


if not _has_ubpe_cython and not _has_ubpe_native:
    raise Exception(
        "Implementation package was not found. Make sure that you are installing the package with optional dependency: `pip install ubpe[native]` or `pip install ubpe[cython]`"
    )


__all__ = ["UBPEClassic", "UBPE"]
