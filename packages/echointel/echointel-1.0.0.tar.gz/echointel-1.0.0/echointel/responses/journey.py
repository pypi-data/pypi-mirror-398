"""Journey response classes for EchoIntel SDK."""

from __future__ import annotations

from typing import Any

from echointel.responses.base import EchoIntelResponse


class Transition(EchoIntelResponse):
    """Markov chain transition between states."""

    from_state: str
    to_state: str
    probability: float
    count: int

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.from_state = data.get("from_state", "")
        self.to_state = data.get("to_state", "")
        self.probability = float(data.get("probability", 0))
        self.count = int(data.get("count", 0))


class MarkovResponse(EchoIntelResponse):
    """Response for journey Markov analysis endpoint."""

    transitions: list[Transition]
    drop_off_probs: dict[str, float]
    interpretation: str

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.transitions = [
            Transition.from_dict(item) for item in data.get("transitions", [])
        ]
        self.drop_off_probs = data.get("drop_off_probs", {})
        self.interpretation = data.get("interpretation", "")


class Path(EchoIntelResponse):
    """Common customer journey path."""

    path: list[str]
    count: int
    conversion_rate: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.path = data.get("path", [])
        self.count = int(data.get("count", 0))
        self.conversion_rate = float(data.get("conversion_rate", 0))


class SequenceResponse(EchoIntelResponse):
    """Response for journey sequences endpoint."""

    paths: list[Path]
    total_journeys: int
    avg_path_length: float

    def _hydrate(self, data: dict[str, Any]) -> None:
        self.paths = [Path.from_dict(item) for item in data.get("paths", [])]
        self.total_journeys = int(data.get("total_journeys", 0))
        self.avg_path_length = float(data.get("avg_path_length", 0))
