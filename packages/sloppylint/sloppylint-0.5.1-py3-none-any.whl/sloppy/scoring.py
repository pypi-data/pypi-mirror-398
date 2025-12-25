"""Slop score calculation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sloppy.patterns.base import Issue


@dataclass
class SlopScore:
    """Slop score breakdown by axis."""

    noise: int = 0
    quality: int = 0
    style: int = 0
    structure: int = 0

    @property
    def total(self) -> int:
        return self.noise + self.quality + self.style + self.structure

    @property
    def verdict(self) -> str:
        if self.total == 0:
            return "CLEAN"
        elif self.total < 25:
            return "ACCEPTABLE"
        elif self.total < 100:
            return "SLOPPY"
        else:
            return "DISASTER"


SEVERITY_WEIGHTS = {
    "critical": 30,
    "high": 15,
    "medium": 8,
    "low": 3,
}


def calculate_score(issues: list["Issue"]) -> SlopScore:
    """Calculate the slop score from issues."""
    score = SlopScore()

    for issue in issues:
        weight = SEVERITY_WEIGHTS.get(issue.severity.value, 3)
        axis = issue.axis

        if axis == "noise":
            score.noise += weight
        elif axis == "quality":
            score.quality += weight
        elif axis == "style":
            score.style += weight
        elif axis == "structure":
            score.structure += weight

    return score
