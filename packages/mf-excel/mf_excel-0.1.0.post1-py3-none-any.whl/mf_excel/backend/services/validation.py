# backend/services/validation.py

from typing import Dict, Any, List
import pandas as pd
import numpy as np
import re

SUPPORTED_SHRINKAGE = {"oas", "oasd", "identity", "monotone diagonal"}
SUPPORTED_FORECASTERS = {"default", "naive", "elastic_net", "ols_pca", "ols"}

def _trailing_horizon_from_df(df: pd.DataFrame) -> int:
    series_cols = [c for c in df.columns if c not in {"Year", "Month", "Quarter", "Week", "Day"}]
    if not series_cols:
        return 0
    is_allna = df[series_cols].isna().all(axis=1).tolist()
    horizon = 0
    for val in reversed(is_allna):
        if val: horizon += 1
        else: break
    return horizon

def _date_fields_present(df: pd.DataFrame) -> bool:
    return any(c in df.columns for c in ["Year", "Month", "Quarter", "Week", "Day"])

def _year_series_parseable(year_series: pd.Series) -> bool:
    if year_series is None or len(year_series) == 0:
        return False
    s = year_series.dropna().astype(object)
    if s.empty:
        return False
    try:
        parsed = pd.to_datetime(s, errors="coerce")
        if parsed.notna().any():
            return True
    except Exception:
        pass
    try:
        numeric = pd.to_numeric(s.astype(str).str.replace(r"\.0+$", "", regex=True), errors="coerce")
        if numeric.notna().any():
            return True
    except Exception:
        pass
    try:
        for v in s.astype(str):
            vstr = v.strip()
            if not vstr:
                continue
            if re.search(r"\b\d{4}[Qq][1-4]\b", vstr):
                return True
            if re.search(r"\b\d{4}M(0[1-9]|1[0-2])\b", vstr):
                return True
            if re.search(r"\b\d{4}W(0[1-9]|[1-4][0-9]|5[0-3])\b", vstr):
                return True
            if re.search(r"\b\d{4}\b", vstr):
                return True
    except Exception:
        pass
    return False

def validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []

    if payload is None:
        errors.append("Missing payload.")
        return {"ok": False, "errors": errors}

    raw_table = payload.get("df") or payload.get("data")
    if raw_table is None:
        errors.append("Missing 'df' or 'data' in payload.")
        return {"ok": False, "errors": errors}

    try:
        df = pd.DataFrame.from_records(raw_table) if isinstance(raw_table, (list, tuple)) else pd.DataFrame(raw_table)
    except Exception as e:
        errors.append(f"df/data is not a valid table: {e}")
        return {"ok": False, "errors": errors}

    if not _date_fields_present(df):
        errors.append("Missing at least one of ['Year','Month','Quarter','Week','Day'] in df.")
    else:
        can_parse_years = _year_series_parseable(df.get("Year")) if "Year" in df.columns else False
        series_cols = [c for c in df.columns if c not in {"Year", "Month", "Quarter", "Week", "Day"}]
        if not can_parse_years:
            if not series_cols:
                errors.append("No series columns found in df.")
            else:
                horizon_rows = _trailing_horizon_from_df(df)
                if horizon_rows == 0 and not any(c in df.columns for c in ["Month", "Quarter", "Week", "Day"]):
                    errors.append(
                        "Date fields are not parseable and no forecast horizon detected: "
                        "provide parseable Year values (YYYY, YYYYQn, YYYYMmm, YYYYWww, ISO date, or Excel serial), "
                        "or include Month/Quarter/Week/Day columns, or leave trailing forecast rows blank."
                    )
        else:
            if not series_cols and "No series columns found in df." not in errors:
                errors.append("No series columns found in df.")
            else:
                horizon_rows = _trailing_horizon_from_df(df)
                if horizon_rows == 0:
                    msg = "No forecast horizon detected: leave trailing forecast rows blank so they are NaN."
                    if msg not in errors:
                        errors.append(msg)

    equality = payload.get("equality_constraints", [])
    inequality = payload.get("inequality_constraints", [])
    if not isinstance(equality, list):
        errors.append("'equality_constraints' must be a list.")
    if not isinstance(inequality, list):
        errors.append("'inequality_constraints' must be a list.")

    shrinkage = str(payload.get("shrinkage_method", "oas")).strip().lower()
    if shrinkage not in SUPPORTED_SHRINKAGE:
        errors.append(f"Unsupported shrinkage_method: {shrinkage}")

    settings = payload.get("settings", {}) if isinstance(payload, dict) else {}
    fore = settings.get("forecaster")
    pca_n = settings.get("pca_n_components")

    if fore is not None and isinstance(fore, str):
        if fore.strip().lower() not in SUPPORTED_FORECASTERS:
            errors.append(f"Unsupported forecaster token: {fore}. Allowed: {sorted(SUPPORTED_FORECASTERS)}")
    if pca_n is not None:
        try:
            val = int(pca_n)
            if val <= 0:
                errors.append("pca_n_components must be a positive integer.")
        except Exception:
            errors.append("pca_n_components must be an integer.")

    default_lam = payload.get("default_lam", -1)
    max_lam = payload.get("max_lam", 129600)
    for name, val in [("default_lam", default_lam), ("max_lam", max_lam)]:
        if not isinstance(val, (int, float, np.integer, np.floating)):
            errors.append(f"'{name}' must be numeric.")

    return {"ok": len(errors) == 0, "errors": errors}
