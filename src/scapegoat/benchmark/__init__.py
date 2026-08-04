"""Behavior-prediction benchmark: schemas, prompts, and aggregation."""

from scapegoat.benchmark.report import BenchmarkReport, aggregate
from scapegoat.benchmark.schema import BenchmarkCase, BenchmarkRun, BenchmarkSet, CaseRun

__all__ = [
    "BenchmarkCase",
    "BenchmarkReport",
    "BenchmarkRun",
    "BenchmarkSet",
    "CaseRun",
    "aggregate",
]
