# profiler/profiler.py
import time
from typing import Dict, List, Optional, Tuple


class Profiler:
    """
    Simple nested-section profiler.

    Usage:
        prof = Profiler()
        with prof.section("load_data"):
            ...
        with prof.section("compute:step1"):
            ...

    prof.total()      -> total exclusive time of all sections
    prof.as_sorted()  -> list of (key, exclusive_time) sorted by time desc
    """

    def __init__(self) -> None:
        # exclusive time per key
        self.t: Dict[str, float] = {}
        # first-seen order (for stable printing if you want it)
        self.order: List[str] = []
        # active Section objects (nesting stack)
        self._stack: List["Section"] = []

    # ---- internal bookkeeping ----
    def add(self, key: str, dt: float) -> None:
        """Accumulate exclusive time for a given key."""
        self.t[key] = self.t.get(key, 0.0) + dt
        if key not in self.order:
            self.order.append(key)

    def section(self, key: str) -> "Section":
        """Return a context manager for profiling a code block."""
        return Section(self, key)

    def _push(self, sect: "Section") -> None:
        self._stack.append(sect)

    def _pop(self, sect: "Section", end_time: float) -> None:
        """
        Pop a section from the stack and attribute exclusive time.

        Handles the (rare) case where exit order doesn't match push order
        by still counting exclusive time but not touching the stack.
        """
        if not self._stack or self._stack[-1] is not sect:
            # stack mismatch: still compute exclusive time
            dt_excl = end_time - sect.t0 - sect._children_time
        else:
            self._stack.pop()
            dt_excl = end_time - sect.t0 - sect._children_time

        # add to this section
        self.add(sect.key, dt_excl)

        # attribute inclusive time (including children) to parent’s children_time
        if self._stack:
            parent = self._stack[-1]
            parent._children_time += (end_time - sect.t0)

    # ---- public API ----
    def total(self) -> float:
        """Total exclusive time over all keys."""
        return sum(self.t.values())

    def as_sorted(self) -> List[Tuple[str, float]]:
        """Return sections sorted by exclusive time descending."""
        return sorted(self.t.items(), key=lambda kv: kv[1], reverse=True)


class Section:
    """
    Context manager representing a single profiled section.
    You usually don't construct this directly; use Profiler.section().
    """

    def __init__(self, prof: Profiler, key: str) -> None:
        self.prof = prof
        self.key = key
        self.t0: float = 0.0
        self._children_time: float = 0.0

    def __enter__(self) -> "Section":
        self.t0 = time.perf_counter()
        self.prof._push(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        t1 = time.perf_counter()
        self.prof._pop(self, t1)


def _fmt_secs(s: float) -> str:
    return f"{s:.6f}s"


def print_profile(title: str, prof: Profiler) -> None:
    """
    Pretty-print a profile summary to stdout.
    """
    total = prof.total()
    print(f"\n[{title}]  total (exclusive sum) = {_fmt_secs(total)}")
    for k, v in prof.as_sorted():
        pct = 100.0 * v / (total if total > 0 else 1.0)
        print(f"  {k:28s} {_fmt_secs(v):>12}  ({pct:5.1f}%)")


def time_block(prof: Optional[Profiler], key: str):
    """
    Convenience helper:

        with time_block(prof, "something"):
            ...

    If prof is None, this is a no-op context manager.
    """
    if prof is None:
        return _NullContext()
    return prof.section(key)


class _NullContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
