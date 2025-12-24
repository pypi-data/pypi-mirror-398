"""boltpy — BOLT: Bibliographic Orchestration for Literature Triage."""

from __future__ import annotations

__version__ = "0.1.0"

from .core import HarvestConfig, HarvestResult, harvest

__all__ = ["__version__", "HarvestConfig", "HarvestResult", "harvest"]
