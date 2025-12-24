"""Top-level package for the new instantgrade architecture.

This package is a skeleton used during an incremental migration.
"""

__all__ = [
    "core",
    "executors",
    "evaluators",
    "reporting",
]

# Lazily export heavy symbols to avoid importing large submodules (and
# their side-effects) during a simple `import instantgrade`.
#
# Historically consumers did: `from instantgrade import Evaluator`. That
# triggered an eager import of the Python evaluator which pulls in
# docker/execution helpers and other heavyweight dependencies. To avoid
# surprising import-time side-effects, we provide a lazy attribute
# loader using PEP 562 (`__getattr__` at package level).

__all__.extend(["InstantGrader"])
__all__.extend(["Evaluator"])


def __getattr__(name: str):

    if name == "InstantGrader":
        from .core.orchestrator import InstantGrader

        return InstantGrader

    if name == "Evaluator":
        # Backwards compatibility: historically users imported Evaluator from
        # the package root (`from instantgrade import Evaluator`). Provide a
        # lazy import to avoid pulling heavy submodules during package import.
        from .evaluators.python.evaluator import Evaluator

        return Evaluator

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    # include lazy attributes in dir() results
    return sorted(list(globals().keys()) + ["InstantGrader", "Evaluator"])
