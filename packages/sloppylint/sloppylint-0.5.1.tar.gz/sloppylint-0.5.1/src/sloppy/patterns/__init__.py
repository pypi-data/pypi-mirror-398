"""Pattern registry."""

from sloppy.patterns.base import BasePattern
from sloppy.patterns.hallucinations import HALLUCINATION_PATTERNS
from sloppy.patterns.noise import NOISE_PATTERNS
from sloppy.patterns.structure import STRUCTURE_PATTERNS
from sloppy.patterns.style import STYLE_PATTERNS


def get_all_patterns() -> list[BasePattern]:
    """Get all registered patterns."""
    return [
        *NOISE_PATTERNS,
        *HALLUCINATION_PATTERNS,
        *STYLE_PATTERNS,
        *STRUCTURE_PATTERNS,
    ]


__all__ = ["get_all_patterns", "BasePattern"]
