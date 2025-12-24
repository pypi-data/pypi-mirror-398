from __future__ import annotations
import numpy as np
import pandas as pd

ALIAS_FREQ = ("f_Hz", "f", "freq", "frequency", "frequency_Hz", "nu", "nu_Hz")
ALIAS_REF = ("phi_ref", "phi_imr", "phi_ref_cal", "phi_ref_raw", "phi_ref_model")
ALIAS_ACT = ("phi_mcgt", "phi_active", "phi_mcgt_cal", "phi_model")


def _mcgt_safe_float(x, default):
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def p95(arr) -> float:
    a = np.asarray(arr, float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return float("nan")
    return float(np.percentile(a, 95.0))


def pick(df: pd.DataFrame, names) -> str | None:
    # exact
    for n in names:
        if n in df.columns:
            return n
    # casefold
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        c = lower.get(n.lower())
        if c:
            return c
    return None


def ensure_fig02_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne un df avec f_Hz, phi_ref, phi_mcgt, phi_active quand c’est possible (sans lever)."""
    out = df.copy()
    fcol = pick(out, ALIAS_FREQ)
    rcol = pick(out, ALIAS_REF)
    acol = pick(out, ALIAS_ACT)

    if fcol and "f_Hz" not in out.columns:
        out["f_Hz"] = out[fcol]
    if rcol and "phi_ref" not in out.columns:
        out["phi_ref"] = out[rcol]

    if acol:
        if "phi_mcgt" not in out.columns:
            out["phi_mcgt"] = out[acol]
        if "phi_active" not in out.columns:
            out["phi_active"] = out[acol]
    else:
        if "phi_active" in out.columns and "phi_mcgt" not in out.columns:
            out["phi_mcgt"] = out["phi_active"]

    return out
