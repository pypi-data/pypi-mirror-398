"""
Katana Meter – Public API

This module provides a stable, import-friendly interface
for backend services, scripts and plugins.

The core engine may evolve internally, but this API
should remain stable across versions.
"""

from typing import Dict, List, Any

from .core import (
    analyze_file,
    analyze_samples,
    AnalysisResult,
    DEFAULT_TARGET_LUFS,
)

__all__ = [
    "analyze_file",
    "analyze_samples",
    "AnalysisResult",
    "DEFAULT_TARGET_LUFS",
]

# ------------------------------------------------------------------
# Optional thin helpers (NON-MANDATORY, but convenient)
# ------------------------------------------------------------------

def analyze(
    path: str,
    target_lufs: float = DEFAULT_TARGET_LUFS
) -> Dict[str, Any]:
    """
    Convenience wrapper around analyze_file().

    This exists purely for readability in backend code:
        from katana_meter.api import analyze
        result = analyze("song.wav")

    It does NOT add logic, state, or side effects.
    """
    return analyze_file(path, target_lufs=target_lufs)


def analyze_raw(
    audio: List[List[float]],
    sr: int,
    target_lufs: float = DEFAULT_TARGET_LUFS
) -> AnalysisResult:
    """
    Analyze already-decoded audio samples.

    Useful when Katana Meter is embedded inside
    another DSP / AI / audio pipeline.
    """
    return analyze_samples(audio, sr, target_lufs=target_lufs)
