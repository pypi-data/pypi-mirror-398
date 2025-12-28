"""Adding this because stats.stats is not properly typed in pstats."""

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from pstats import Stats as _Stats

    class Stats(_Stats):
        """Extended Stats class with stats attribute."""

        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

        stats: dict[str, tuple[Any, ...]]  # pyright: ignore[reportIncompatibleVariableOverride]

else:
    Stats = lazy("pstats", "Stats")
