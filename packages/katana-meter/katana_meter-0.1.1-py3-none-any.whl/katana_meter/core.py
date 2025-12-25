# -*- coding: utf-8 -*-
# Katana Meter
# Copyright (C) 2025 Katana Project
# Licensed under the GNU General Public License v3.0


"""
Katana Meter – Core Engine

Deterministic audio analysis engine:
- Integrated LUFS (gated, BS.1770-inspired)
- Sample Peak (dBTP-approx)
- Gain to target LUFS
- ΔE entropy-change metric (0..1 scaled)

No external Python dependencies.
WAV native. MP3/FLAC/etc require optional ffmpeg.
"""


from __future__ import annotations

import os
import math
import wave
import struct
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------

DEFAULT_TARGET_LUFS = -14.0
DEFAULT_DECODE_SR = 48000
DEFAULT_DECODE_CH = 2

SILENCE_EPS = 1e-9
MIN_DURATION_FOR_LUFS_SEC = 0.40  # 400ms

# ------------------------------------------------------------------
# Utils
# ------------------------------------------------------------------

def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def guess_format(path: str) -> str:
    _, ext = os.path.splitext(path)
    return ext.lower().lstrip(".") or "unknown"


def safe_remove(path: str) -> None:
    try:
        os.remove(path)
    except Exception:
        pass


def db20(x: float) -> float:
    return 20.0 * math.log10(max(x, 1e-12))


def db10(x: float) -> float:
    return 10.0 * math.log10(max(x, 1e-18))

# ------------------------------------------------------------------
# Decode / Read
# ------------------------------------------------------------------

def decode_to_wav_if_needed(
    path: str,
    target_sr: int = DEFAULT_DECODE_SR,
    target_ch: int = DEFAULT_DECODE_CH,
) -> Tuple[str, Optional[str], Dict[str, Any]]:

    src_format = guess_format(path)

    if path.lower().endswith(".wav"):
        return path, None, {
            "decoder": "wav-native",
            "src_format": src_format,
            "dst_sr": None,
            "dst_ch": None,
        }

    if not has_ffmpeg():
        raise RuntimeError("Non-WAV input requires ffmpeg")

    tmp = "_katana_tmp_decode.wav"

    cmd = [
        "ffmpeg", "-y",
        "-i", path,
        "-ac", str(target_ch),
        "-ar", str(target_sr),
        "-f", "wav",
        tmp
    ]

    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg decode failed")

    return tmp, tmp, {
        "decoder": "ffmpeg",
        "src_format": src_format,
        "dst_sr": target_sr,
        "dst_ch": target_ch,
    }


def read_wav_float(path: str) -> Tuple[List[List[float]], int]:
    with wave.open(path, "rb") as wf:
        ch = wf.getnchannels()
        sr = wf.getframerate()
        sw = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())

    audio: List[List[float]] = [[] for _ in range(ch)]

    if sw == 2:
        data = struct.unpack("<" + "h" * (len(raw) // 2), raw)
        for i, s in enumerate(data):
            audio[i % ch].append(s / 32768.0)

    elif sw == 3:
        for i in range(0, len(raw), 3):
            v = raw[i] | (raw[i + 1] << 8) | (raw[i + 2] << 16)
            if v & 0x800000:
                v -= 0x1000000
            audio[(i // 3) % ch].append(v / 8388608.0)

    elif sw == 4:
        data = struct.unpack("<" + "i" * (len(raw) // 4), raw)
        for i, s in enumerate(data):
            audio[i % ch].append(s / 2147483648.0)

    else:
        raise RuntimeError("Unsupported WAV format")

    return audio, sr

# ------------------------------------------------------------------
# Labels / Warnings
# ------------------------------------------------------------------

def label_loudness(lufs: float) -> str:
    if lufs > -11.0:
        return "very loud"
    if lufs > -14.0:
        return "loud"
    if lufs > -18.0:
        return "balanced"
    return "dynamic"


def label_peak_risk(peak_db: float) -> str:
    if peak_db >= 0.0:
        return "clipping risk"
    if peak_db >= -1.0:
        return "encode risk"
    return "safe"


def label_gain_action(gain_db: float) -> str:
    if gain_db > 2.0:
        return "needs lift"
    if gain_db < -2.0:
        return "needs trim"
    return "near target"


def build_warnings(lufs: float, peak_db: float) -> List[str]:
    warns: List[str] = []
    if peak_db >= 0.0:
        warns.append("Peak >= 0 dBFS: clipping / encode overflow risk")
    elif peak_db >= -1.0:
        warns.append("Peak near -1 dBFS: encode overflow possible")
    if lufs > -11.0:
        warns.append("Very loud content: platforms will normalize aggressively")
    return warns

# ------------------------------------------------------------------
# DSP Metrics
# ------------------------------------------------------------------

def dc_remove(ch: List[float]) -> List[float]:
    if not ch:
        return ch
    m = sum(ch) / len(ch)
    return [v - m for v in ch]


def is_silent(audio: List[List[float]]) -> bool:
    for ch in audio:
        for v in ch[:50000]:
            if abs(v) > SILENCE_EPS:
                return False
    return True


def sample_peak_db(audio: List[List[float]]) -> float:
    peak = 0.0
    for ch in audio:
        for v in ch:
            if abs(v) > peak:
                peak = abs(v)
    return db20(peak)


def integrated_lufs(audio: List[List[float]], sr: int) -> float:
    block = int(sr * 0.400)
    step = int(sr * 0.100)

    if len(audio[0]) < block:
        raise RuntimeError("Audio too short for LUFS")

    def ms_to_lufs(ms: float) -> float:
        return -0.691 + db10(ms)

    blocks: List[float] = []

    for i in range(0, len(audio[0]) - block + 1, step):
        ms = 0.0
        for ch in audio:
            seg = ch[i:i + block]
            ms += sum(v * v for v in seg) / block
        blocks.append(ms / len(audio))

    gated = [b for b in blocks if ms_to_lufs(b) > -70]
    mean = sum(gated) / len(gated)
    gate = ms_to_lufs(mean) - 10
    final = [b for b in gated if ms_to_lufs(b) > gate]

    return ms_to_lufs(sum(final) / len(final))


def delta_e(audio: List[List[float]], sr: int) -> float:
    mono = audio[0] if len(audio) == 1 else [
        (audio[0][i] + audio[1][i]) * 0.5 for i in range(len(audio[0]))
    ]

    size = max(int(sr * 0.100), 16)
    diffs: List[float] = []
    prev: Optional[float] = None

    for i in range(0, len(mono) - size, size):
        blk = mono[i:i + size]
        mags = [abs(v) for v in blk]
        mx = max(mags)

        if mx < 1e-12:
            h = 0.0
        else:
            hist = [0] * 32
            for m in mags:
                hist[int((m / mx) * 31)] += 1
            h = 0.0
            for c in hist:
                if c:
                    p = c / len(mags)
                    h -= p * math.log(p, 2)

        if prev is not None:
            diffs.append(abs(h - prev))
        prev = h

    return min(sum(diffs) / len(diffs), 1.0) if diffs else 0.0

# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

@dataclass
class AnalysisResult:
    lufs: float
    peak_dbtp_approx: float
    gain_to_target_db: float
    delta_e: float
    target_lufs: float
    labels: Dict[str, str]
    warnings: List[str]
    info: Dict[str, Any]


def analyze_samples(
    audio: List[List[float]],
    sr: int,
    target_lufs: float = DEFAULT_TARGET_LUFS
) -> AnalysisResult:

    if not audio or not audio[0]:
        raise ValueError("Empty audio")

    if len(audio) == 1:
        audio = [audio[0], audio[0][:]]

    if is_silent(audio):
        raise ValueError("Audio is silent")

    audio = [dc_remove(ch) for ch in audio]

    if len(audio[0]) < int(sr * MIN_DURATION_FOR_LUFS_SEC):
        raise ValueError("Audio too short")

    lufs = integrated_lufs(audio, sr)
    peak = sample_peak_db(audio)
    gain = target_lufs - lufs
    de = delta_e(audio, sr)

    return AnalysisResult(
        lufs=lufs,
        peak_dbtp_approx=peak,
        gain_to_target_db=gain,
        delta_e=de,
        target_lufs=target_lufs,
        labels={
            "loudness": label_loudness(lufs),
            "peak_risk": label_peak_risk(peak),
            "gain_action": label_gain_action(gain),
        },
        warnings=build_warnings(lufs, peak),
        info={
            "sr": sr,
            "channels": len(audio),
            "peak_kind": "sample-peak (approx)",
            "lufs_kind": "integrated gated",
            "delta_e_kind": "entropy-change",
        }
    )


def analyze_file(path: str, target_lufs: float = DEFAULT_TARGET_LUFS) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    tmp = None
    try:
        wav, tmp, decode_info = decode_to_wav_if_needed(path)
        audio, sr = read_wav_float(wav)
        res = analyze_samples(audio, sr, target_lufs)

        return {
            "lufs": round(res.lufs, 3),
            "peak_dbtp_approx": round(res.peak_dbtp_approx, 3),
            "gain_to_target_db": round(res.gain_to_target_db, 3),
            "delta_e": round(res.delta_e, 5),
            "target_lufs": target_lufs,
            "labels": res.labels,
            "warnings": res.warnings,
            "info": {**res.info, **decode_info},
        }

    finally:
        if tmp:
            safe_remove(tmp)


__all__ = [
    "analyze_file",
    "analyze_samples",
    "AnalysisResult",
    "DEFAULT_TARGET_LUFS",
]
