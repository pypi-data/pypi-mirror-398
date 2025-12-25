from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine import MimaEngine


class MimaView:
    """Base class for all view related classes."""

    engine: MimaEngine
