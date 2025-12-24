from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional


LEDGER_DIR = Path.cwd() / ".carbon_ledger"
LEDGER_PATH = LEDGER_DIR / "ledger.jsonl"


def _stable_dumps(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _compute_hash(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_stable_dumps(payload).encode("utf-8")).hexdigest()


def _read_tail_hash() -> Optional[str]:
    if not LEDGER_PATH.exists():
        return None
    last = None
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                last = rec.get("entry_hash")
            except Exception:
                continue
    return last


@dataclass
class CarbonRecord:
    project: str
    task: str
    created_at: str
    duration_ms: float
    energy_kwh_compute: float
    energy_kwh_llm: float
    energy_kwh_total: float
    co2e_g_total: float
    carbon_minutes: float
    llm_tokens: int
    metadata: Dict[str, Any]
    prev_hash: Optional[str]
    entry_hash: Optional[str] = None


def _estimate_energy(*, llm_tokens: int) -> Dict[str, float]:
    energy_wh_compute = float(os.environ.get("ENERGY_WH_PER_RUN", "0.7"))
    llm_wh_per_1k = float(os.environ.get("LLM_WH_PER_1K_TOKENS", "0.002"))
    energy_wh_llm = (llm_tokens / 1000.0) * llm_wh_per_1k
    energy_kwh_compute = energy_wh_compute / 1000.0
    energy_kwh_llm = energy_wh_llm / 1000.0
    energy_kwh_total = energy_kwh_compute + energy_kwh_llm
    co2_g_per_kwh = float(os.environ.get("CO2_G_PER_KWH", "385.0"))
    co2e_g_total = energy_kwh_total * co2_g_per_kwh

    # Carbon Minute: prefer explicit kWh per minute reference if provided (kettle baseline),
    # otherwise fall back to legacy baseline kW method for backward compatibility.
    kwh_ref_env = os.environ.get("CARBON_MINUTE_KWH_PER_MIN")
    conv_ver_env = os.environ.get("CARBON_CONVERSION_VERSION")
    if kwh_ref_env:
        try:
            kwh_ref_val = float(kwh_ref_env)
        except Exception:
            kwh_ref_val = 0.03667  # safe default (2.2kW kettle minute)
        carbon_minutes = energy_kwh_total / max(kwh_ref_val, 1e-12)
        conversion_version = conv_ver_env or "kettle-default-v1"
    else:
        baseline_kw = float(os.environ.get("CARBON_MINUTE_KW_BASELINE", "1.0"))
        carbon_minutes = (energy_kwh_total / max(baseline_kw, 1e-9)) * 60.0
        kwh_ref_val = baseline_kw / 60.0  # implied reference for transparency
        conversion_version = conv_ver_env or "baseline-kw-legacy"

    return {
        "energy_kwh_compute": energy_kwh_compute,
        "energy_kwh_llm": energy_kwh_llm,
        "energy_kwh_total": energy_kwh_total,
        "co2e_g_total": co2e_g_total,
        "carbon_minutes": carbon_minutes,
        "kwh_reference_minute": kwh_ref_val,
        "conversion_version": conversion_version,
    }


def _append_record(rec: CarbonRecord) -> Dict[str, Any]:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    base = asdict(rec)
    base_no_hash = {k: v for k, v in base.items() if k != "entry_hash"}
    entry_hash = _compute_hash(base_no_hash)
    base["entry_hash"] = entry_hash
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(_stable_dumps(base) + "\n")
    return base


def verify_ledger() -> bool:
    """Verify entire ledger chain integrity.

    Returns True if the chain is valid; False otherwise.
    """
    if not LEDGER_PATH.exists():
        return True
    prev_hash: Optional[str] = None
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            # recompute hash without entry_hash
            entry_hash = rec.get("entry_hash")
            payload = {k: v for k, v in rec.items() if k != "entry_hash"}
            # check prev pointer
            if payload.get("prev_hash") != prev_hash:
                return False
            # recompute current
            if _compute_hash(payload) != entry_hash:
                return False
            prev_hash = entry_hash
    return True


def verify_ledger_cli() -> None:
    ok = verify_ledger()
    print("ledger: VALID" if ok else "ledger: CORRUPT", file=sys.stderr)
    sys.exit(0 if ok else 2)


def track_carbon(project: str, task: str, *, tags: Optional[Dict[str, Any]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that logs energy/carbon metrics for the wrapped function.

    The wrapped function may return a dict containing 'llm_tokens' to account for
    language model energy. If absent, 0 is assumed.
    """

    def _decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            res = None
            err: Optional[Exception] = None
            try:
                res = fn(*args, **kwargs)
                return res
            except Exception as e:  # propagate after logging duration
                err = e
                raise
            finally:
                duration_ms = (time.perf_counter() - start) * 1000.0
                llm_tokens = 0
                if isinstance(res, dict):
                    try:
                        llm_tokens = int(res.get("llm_tokens", 0))
                    except Exception:
                        llm_tokens = 0
                est = _estimate_energy(llm_tokens=llm_tokens)
                prev_hash = _read_tail_hash()
                record = CarbonRecord(
                    project=project,
                    task=task,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    duration_ms=duration_ms,
                    energy_kwh_compute=est["energy_kwh_compute"],
                    energy_kwh_llm=est["energy_kwh_llm"],
                    energy_kwh_total=est["energy_kwh_total"],
                    co2e_g_total=est["co2e_g_total"],
                    carbon_minutes=est["carbon_minutes"],
                    llm_tokens=llm_tokens,
                    metadata={
                        "tags": tags or {},
                        "error": str(err) if err else None,
                        "conversion_version": est.get("conversion_version"),
                        "kWh_reference_minute": est.get("kwh_reference_minute"),
                        "uncertainty_band": os.environ.get("CARBON_UNCERTAINTY_BAND"),
                        "calibration_version": os.environ.get("CALIBRATION_VERSION"),
                        "kWh_request": est["energy_kwh_total"],
                    },
                    prev_hash=prev_hash,
                )
                _append_record(record)
        return _wrapped

    return _decorate
