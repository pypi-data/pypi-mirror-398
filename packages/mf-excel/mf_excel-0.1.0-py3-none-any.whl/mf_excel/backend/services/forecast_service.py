# backend/services/forecast_service.py

import logging
import sys
from typing import Dict, List, Optional, Any, Tuple
import importlib
import re
import math

import numpy as np
import pandas as pd
from sktime.exceptions import NotFittedError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a custom formatter that forces flush
class FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)

# Ensure logger has a console handler with auto-flush
if not logger.handlers:
    handler = FlushingStreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)s: %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Also configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)


class PreprocessingForecaster:
    """A thin wrapper to coerce X to numeric and drop empty X."""

    def __init__(self, inner_forecaster: Any):
        self.inner = inner_forecaster

    def __repr__(self):
        try:
            if hasattr(self.inner, "steps") and self.inner.steps:
                last = self.inner.steps[-1][1]
                est = getattr(last, "estimator", last)
                return f"PreprocessingForecaster(inner={repr(est)})"
            return f"PreprocessingForecaster(inner={repr(self.inner)})"
        except Exception:
            return "PreprocessingForecaster(inner=...)"

    def _preprocess_X(self, X):
        if X is None:
            return None
        try:
            df = pd.DataFrame(X)
        except Exception:
            return X
        # coerce to numeric where possible
        num = df.select_dtypes(include=[np.number])
        if num.shape[1] == 0:
            coerced = df.apply(lambda col: pd.to_numeric(col, errors="coerce"))
            num = coerced.select_dtypes(include=[np.number])
        num = num.fillna(0)
        # if no columns remain, return None so forecaster fits univariate
        return None if num.shape[1] == 0 else num

    def fit(self, y, X=None, fh=None):
        X2 = self._preprocess_X(X)
        return self.inner.fit(y=y, X=X2, fh=fh)

    def predict(self, X=None, fh=None):
        X2 = self._preprocess_X(X)
        return self.inner.predict(X=X2, fh=fh)





def _instantiate_forecaster(
    token: Any,
    *,
    pca_n_components: Optional[int] = None,
    has_exog: bool = False,
):
    """Instantiate a sktime forecaster from a token. Avoid X-dependent models if no exog.
    
    Returns tuple of (forecaster_object, actual_forecaster_name_used).
    If token is None or 'default', returns None to allow MFF to use its built-in DefaultForecaster
    which uses sktime's ForecastingGridSearchCV ensemble.
    """
    if token is None:
        logger.info("_instantiate_forecaster: token is None, returning None for MFF's DefaultForecaster")
        return None, "default"
    if not isinstance(token, str):
        logger.info("_instantiate_forecaster: token is not string, returning as-is: %s", type(token))
        return token, None
    t = token.strip().lower()
    logger.info("_instantiate_forecaster: token='%s', has_exog=%s", t, has_exog)
    if t in ("none", ""):
        logger.info("_instantiate_forecaster: token is none/empty, returning None for MFF's DefaultForecaster")
        return None, "default"
    if t == "default":
        logger.info("_instantiate_forecaster: token is 'default', returning None for MFF's DefaultForecaster")
        return None, "default"
    try:
        if t == "naive":
            logger.info("_instantiate_forecaster: instantiating NaiveForecaster")
            from sktime.forecasting.naive import NaiveForecaster
            from sktime.forecasting.compose import ForecastingPipeline

            return ForecastingPipeline(steps=[("naive", NaiveForecaster())]), "naive"

        if t == "elastic_net":
            if not has_exog:
                logger.warning("_instantiate_forecaster: elastic_net requires exogenous variables (multiple series), but only single series found. Falling back to naive forecaster.")
                logger.info("_instantiate_forecaster: instantiating NaiveForecaster (fallback)")
                from sktime.forecasting.naive import NaiveForecaster
                from sktime.forecasting.compose import ForecastingPipeline
                return ForecastingPipeline(steps=[("naive", NaiveForecaster())]), "naive"
            logger.info("_instantiate_forecaster: instantiating ElasticNet")
            from sklearn.linear_model import ElasticNet
            from sktime.forecasting.compose import ForecastingPipeline, DirectReductionForecaster

            return ForecastingPipeline(
                steps=[("elastic", DirectReductionForecaster(ElasticNet()))]
            ), "elastic_net"

        if t == "ols_pca":
            if not has_exog:
                logger.warning("_instantiate_forecaster: ols_pca requires exogenous variables (multiple series), but only single series found. Falling back to naive forecaster.")
                logger.info("_instantiate_forecaster: instantiating NaiveForecaster (fallback)")
                from sktime.forecasting.naive import NaiveForecaster
                from sktime.forecasting.compose import ForecastingPipeline
                return ForecastingPipeline(steps=[("naive", NaiveForecaster())]), "naive"
            logger.info("_instantiate_forecaster: instantiating OLS_PCA with n_components=%s", pca_n_components)
            from sklearn.decomposition import PCA
            from sklearn.linear_model import LinearRegression
            from sktime.forecasting.compose import ForecastingPipeline, DirectReductionForecaster

            n_comp = int(pca_n_components) if (pca_n_components and int(pca_n_components) > 0) else 1
            from sktime.transformations.series.adapt import TabularToSeriesAdaptor

            pipeline = ForecastingPipeline(
                steps=[
                    ("pca", TabularToSeriesAdaptor(PCA(n_components=n_comp))),
                    ("ols", DirectReductionForecaster(LinearRegression())),
                ]
            )
            return PreprocessingForecaster(pipeline), "ols_pca"

        if t == "ols":
            if not has_exog:
                logger.warning("_instantiate_forecaster: ols requires exogenous variables (multiple series), but only single series found. Falling back to naive forecaster.")
                logger.info("_instantiate_forecaster: instantiating NaiveForecaster (fallback)")
                from sktime.forecasting.naive import NaiveForecaster
                from sktime.forecasting.compose import ForecastingPipeline
                return ForecastingPipeline(steps=[("naive", NaiveForecaster())]), "naive"
            logger.info("_instantiate_forecaster: instantiating OLS")
            from sklearn.linear_model import LinearRegression
            from sktime.forecasting.compose import ForecastingPipeline, DirectReductionForecaster

            pipeline = ForecastingPipeline(
                steps=[("ols", DirectReductionForecaster(LinearRegression()))]
            )
            return PreprocessingForecaster(pipeline), "ols"
    except Exception as e:
        logger.exception("_instantiate_forecaster: exception for token='%s': %s", t, str(e))
        return None, None
    logger.warning("_instantiate_forecaster: unknown token '%s', returning None", t)
    return None, None


def _safe_for_json(obj: Any) -> Any:
    """Convert objects to JSON-safe primitives."""
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or not math.isfinite(obj):
            return None
    if isinstance(obj, (str, int, bool)):
        return obj
    try:
        if isinstance(obj, np.generic):
            return _safe_for_json(obj.item())
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {str(k): _safe_for_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_safe_for_json(v) for v in obj]
        if isinstance(obj, pd.DataFrame):
            return {
                "columns": list(obj.columns.astype(str)),
                "data": [[_safe_for_json(v) for v in row.tolist()] for _, row in obj.reset_index(drop=True).iterrows()],
            }
        if isinstance(obj, pd.Series):
            return [_safe_for_json(v) for v in obj.tolist()]
    except Exception:
        pass
    try:
        return str(obj)
    except Exception:
        return None


def _infer_index_frequency(ts_index: pd.DatetimeIndex) -> str:
    """Infer frequency hint: 'A', 'Q', 'M', 'W', 'D', or 'O'."""
    try:
        freq = pd.infer_freq(ts_index)
        if freq is None:
            months = sorted({d.month for d in ts_index[:12]})
            if months == [1]:
                return "A"
            if set(months).issubset({1, 4, 7, 10}):
                return "Q"
            if 1 < len(months) <= 12:
                return "M"
            if len(ts_index) > 30:
                return "D"
            return "O"
        if freq.startswith(("A", "Y")):
            return "A"
        if freq.startswith("Q"):
            return "Q"
        if freq.startswith("M"):
            return "M"
        if freq.startswith("W"):
            return "W"
        if freq.startswith("D"):
            return "D"
        return "O"
    except Exception:
        return "O"


def _timestamp_to_period_token(ts: pd.Timestamp, freq_hint: Optional[str] = None) -> str:
    """Convert Timestamp to a token string macroframe_forecast understands."""
    if ts is None or pd.isna(ts):
        return ""
    freq_hint = freq_hint or "O"
    try:
        if freq_hint == "A":
            return f"{ts.year}"
        if freq_hint == "Q":
            q = (ts.month - 1) // 3 + 1
            return f"{ts.year}Q{q}"
        if freq_hint == "M":
            return f"{ts.year}M{ts.month:02d}"
        if freq_hint == "W":
            w = ts.isocalendar().week
            return f"{ts.year}W{int(w):02d}"
        return ts.strftime("%Y_%m_%d")
    except Exception:
        return ts.strftime("%Y_%m_%d")


def _parse_to_timestamp(val) -> Optional[pd.Timestamp]:
    """Parse Year-like cell values to Timestamp, supporting tokens and serials."""
    if val is None:
        return None
    try:
        if isinstance(val, pd.Timestamp):
            return val
    except Exception:
        pass
    s = str(val).strip()

    # Quarterly token: YYYYQn
    try:
        m = re.match(r"^(\d{4})[Qq]([1-4])$", s)
        if m:
            per = pd.Period(f"{m.group(1)}Q{m.group(2)}", freq="Q")
            return per.to_timestamp(how="start")
    except Exception:
        pass

    # Monthly token: YYYYMmm
    try:
        m = re.match(r"^(\d{4})M(0[1-9]|1[0-2])$", s)
        if m:
            return pd.Timestamp(year=int(m.group(1)), month=int(m.group(2)), day=1)
    except Exception:
        pass

    # Weekly token: YYYYWww (ISO week)
    try:
        m = re.match(r"^(\d{4})W(0[1-9]|[1-4][0-9]|5[0-3])$", s)
        if m:
            year = int(m.group(1))
            week = int(m.group(2))
            return pd.to_datetime(f"{year}-W{week:02d}-1", format="%G-W%V-%u", errors="coerce")
    except Exception:
        pass

    # Excel serial (rough guard)
    try:
        if isinstance(val, (int, float)) and abs(float(val)) < 1e6:
            base = pd.Timestamp("1899-12-30")
            return base + pd.to_timedelta(int(val), unit="D")
    except Exception:
        pass

    # Fallback to generic parsing
    try:
        parsed = pd.to_datetime(val, errors="coerce", dayfirst=False)
        if not pd.isna(parsed):
            return parsed
    except Exception:
        pass
    return None


def _normalize_constraint_with_freq(expr: str, freq_hint: Optional[str]) -> str:
    """
    Normalise constraint expression.
    
    Rules:
    1. Explicit wildcards (Series?) are preserved for all periods
    2. Specific date constraints (Series_2024, Series_2024Q3, etc.) are preserved as specific period constraints
    3. Only convert '=' to difference form '- (value)'
    4. Ensure parentheses around RHS constants for MFF compatibility
    
    Examples:
    - 'pb? - rev? + exp?' -> 'pb? - rev? + exp?' (wildcard, applies to all periods)
    - 'exp_2030 - 37' -> 'exp_2030 - (37)' (specific, applies only to 2030)
    - 'GDP_2024Q3 = 700000' -> 'GDP_2024Q3 - (700000)' (specific, applies only to 2024Q3)
    - 'GDP_2030 - 1.04*GDP_2029' -> 'GDP_2030 - (1.04*GDP_2029)' (specific relationship)
    - 'pb? - rev? + exp?' -> 'pb? - rev? + exp?' (wildcard identity, all periods)
    - 'exp_2030 - rev_2030 + int_2030' -> 'exp_2030 - rev_2030 + int_2030' (specific expression)
    """
    if not expr or not isinstance(expr, str):
        return expr
    s = str(expr)

    # Convert simple equality into difference form ONLY for single RHS values
    # Don't convert if RHS contains operators or multiple variables
    if re.search(r"(?<![<>])=(?![<>])", s):
        lhs, rhs = s.split("=", 1)
        rhs = rhs.strip()
        # Only wrap in parentheses if it's a simple numeric value (no operators except +/- sign)
        # Check if RHS is a simple number or a formula with operators
        if re.match(r'^[+-]?\d+\.?\d*$', rhs) or (re.match(r'^[+-]?\d', rhs) and '*' not in rhs and not any(c.isalpha() for c in rhs)):
            # Simple number: wrap in parentheses
            s = f"{lhs.strip()} - ({rhs})"
        else:
            # Complex expression: wrap entire RHS
            s = f"{lhs.strip()} - ({rhs})"
    
    # For expressions already with '-', determine if RHS needs wrapping
    elif " - " in s:
        parts = s.split(" - ", 1)
        if len(parts) == 2:
            lhs, rhs = parts
            rhs = rhs.strip()
            
            # Don't wrap if already wrapped in parentheses
            if not rhs.startswith("("):
                # Check if RHS has top-level additive operators (+ or -)
                # These indicate multi-term expressions that should NOT be wrapped
                # Examples: "rev_2030 + int_2030" or "a - b + c"
                # But NOT: "1.04*GDP_2029" or "-37" or "100"
                
                # Simple heuristic: if RHS contains ' + ' or ' - ' (with spaces), it's multi-term
                if ' + ' in rhs or ' - ' in rhs:
                    # Multi-term expression, don't wrap
                    s = f"{lhs} - {rhs}"
                else:
                    # Single term: number, variable, or multiplicative expression
                    # All should be wrapped for MFF compatibility
                    s = f"{lhs} - ({rhs})"
    
    return s


def _apply_equality_constraints_to_fallback(df: pd.DataFrame, eq_constraints: List[str], freq_hint: Optional[str]) -> pd.DataFrame:
    """
    Apply equality constraints to fallback forecast results.
    
    Constraints are expected in normalized form like:
    - "Sales_2021_01_01 - (120)"  (value should be 120)
    - "Cost_2022_01_01 - (150)"   (value should be 150)
    """
    if not eq_constraints or df.empty:
        return df
    
    df_result = df.copy()
    
    for constraint in eq_constraints:
        try:
            # Parse constraint: "Series_YYYY_MM_DD - (value)"
            if " - (" not in constraint:
                continue
            
            lhs_part, rhs_part = constraint.split(" - (", 1)
            lhs_part = lhs_part.strip()
            rhs_part = rhs_part.rstrip(")").strip()
            
            try:
                target_value = float(rhs_part)
            except ValueError:
                logger.debug(f"Could not parse constraint value: {rhs_part}")
                continue
            
            # Extract series name and date from "Series_YYYY_MM_DD" format
            # Need to find where the date pattern starts (e.g., "2021_01_01")
            import re as _re
            date_pattern = r'_(\d{4})_(\d{1,2})_(\d{1,2})$'
            match = _re.search(date_pattern, lhs_part)
            
            if match:
                year_str = match.group(1)
                month_str = match.group(2)
                day_str = match.group(3)
                series_name = lhs_part[:match.start()]  # Everything before the date
                
                try:
                    target_date = pd.Timestamp(year=int(year_str), month=int(month_str), day=int(day_str))
                except (ValueError, TypeError):
                    logger.debug(f"Could not parse date from constraint: {lhs_part}")
                    continue
                
                # Find matching row by timestamp and apply constraint
                if series_name in df_result.columns:
                    # Find row closest to target date
                    if isinstance(df_result.index, (pd.DatetimeIndex, pd.PeriodIndex)):
                        # Convert PeriodIndex to DatetimeIndex if needed
                        if isinstance(df_result.index, pd.PeriodIndex):
                            idx = df_result.index.to_timestamp()
                        else:
                            idx = df_result.index
                        
                        # Find the row matching the target date
                        mask = idx == target_date
                        if mask.any():
                            df_result.loc[mask, series_name] = target_value
                            logger.info(f"Applied constraint: {series_name} at {target_date} = {target_value}")
                        else:
                            logger.debug(f"No matching date {target_date} found for constraint on {series_name}")
                    else:
                        logger.debug(f"Index type {type(df_result.index)} not supported for constraint application")
                else:
                    logger.debug(f"Series {series_name} not found in columns {list(df_result.columns)} for constraint")
            else:
                logger.debug(f"Could not parse date pattern from constraint LHS: {lhs_part}")
        except Exception as e:
            logger.debug(f"Error applying constraint '{constraint}': {str(e)}")
            continue
    
    return df_result


def _simple_forecast_fallback(df_mff: pd.DataFrame, eq_constraints: Optional[List[str]] = None, 
                             freq_hint: Optional[str] = None) -> pd.DataFrame:
    """
    Fallback forecasting when MFF library fails.
    Uses last observation carried forward (LOCF) for empty cells.
    Applies equality constraints if provided.
    """
    logger.info("Using simple forecast fallback: Last Observation Carried Forward (LOCF)")
    df = df_mff.copy()
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    
    # Forward fill for each numeric column
    for col in numeric_cols:
        df[col] = df[col].ffill()  # Use ffill() instead of deprecated fillna(method='ffill')
        # If still NaN at the start, use the mean or a default value
        if df[col].isna().any():
            mean_val = df[col].dropna().mean() if df[col].dropna().shape[0] > 0 else 0
            df[col] = df[col].fillna(mean_val)
    
    # Apply equality constraints to the fallback forecast
    if eq_constraints:
        df = _apply_equality_constraints_to_fallback(df, eq_constraints, freq_hint)
    
    # Reset index to make sure timestamps are preserved
    # df_mff has DatetimeIndex, so preserve it
    return df


def run_forecast(
    df: object,
    equality_constraints: Optional[List[str]] = None,
    inequality_constraints: Optional[List[str]] = None,
    shrinkage_method: Any = "oas",
    default_lam: float = -1,
    max_lam: float = 129600,
    parallelize: bool = True,
    forecaster: Optional[Any] = None,
    horizon_override: Optional[int] = None,
    pca_n_components: Optional[int] = None,
) -> Dict[str, Any]:
    logger.info("run_forecast called")

    equality_constraints = equality_constraints or []
    inequality_constraints = inequality_constraints or []

    # Coerce incoming data to DataFrame
    df_work = df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    df_work = df_work.where(pd.notnull(df_work), np.nan)

    # Build per-row timestamp from fields, including Day support
    def _compose_timestamp_from_fields(row: pd.Series) -> Optional[pd.Timestamp]:
        y = row.get("Year", None)
        m = row.get("Month", None)
        q = row.get("Quarter", None)
        w = row.get("Week", None)
        d = row.get("Day", None)

        def _to_int(x):
            try:
                return int(float(x))
            except Exception:
                return None

        yi = _to_int(y)
        mi = _to_int(m)
        qi = _to_int(q)
        wi = _to_int(w)
        di = _to_int(d)
        try:
            if yi is not None and qi in (1, 2, 3, 4):
                per = pd.Period(f"{yi}Q{qi}", freq="Q")
                return per.to_timestamp(how="start")
            if yi is not None and mi is not None and 1 <= mi <= 12 and di is not None and 1 <= di <= 31:
                return pd.Timestamp(year=yi, month=mi, day=di)
            if yi is not None and mi is not None and 1 <= mi <= 12:
                return pd.Timestamp(year=yi, month=mi, day=1)
            if yi is not None and wi is not None and 1 <= wi <= 53:
                return pd.to_datetime(f"{yi}-W{int(wi):02d}-1", format="%G-W%V-%u", errors="coerce")
            if yi is not None:
                return pd.Timestamp(year=yi, month=1, day=1)
        except Exception:
            return None
        return None

    # Primary timestamp composition
    df_work["_ts_"] = df_work.apply(_compose_timestamp_from_fields, axis=1)
    if df_work["_ts_"].isna().all() and "Year" in df_work.columns:
        # Fallback: parse Year directly (tokens like 2024Q1)
        df_work["_ts_"] = pd.to_datetime(df_work["Year"], errors="coerce")

    # Drop totally empty rows and rows without Year/_ts_ where possible
    if "Year" in df_work.columns:
        df_work = df_work[df_work["Year"].notna()]
    df_work = df_work.dropna(how="all")

    # Series to numeric
    date_cols = [c for c in ["Year", "Month", "Quarter", "Week", "Day"] if c in df_work.columns]
    series_cols = [c for c in df_work.columns if c not in date_cols + ["_ts_"]]
    for col in series_cols:
        df_work[col] = pd.to_numeric(df_work[col], errors="coerce").astype(float)

    # Token view (for constraints normalisation)
    df_tokens = df_work[df_work["_ts_"].notna()].copy()
    freq_hint = None
    try:
        if not df_tokens.empty:
            dt_index = pd.DatetimeIndex(df_tokens["_ts_"].tolist())
            freq_hint = _infer_index_frequency(dt_index)
    except Exception:
        freq_hint = None

    def _ts_to_token(ts):
        if pd.isna(ts) or ts is None:
            return None
        if not isinstance(ts, pd.Timestamp):
            ts = pd.to_datetime(ts, errors="coerce")
        return _timestamp_to_period_token(ts, freq_hint=freq_hint)

    df_tokens_view = df_tokens.copy()
    df_tokens_view["_token_"] = df_tokens_view["_ts_"].apply(_ts_to_token)
    df_tokens_view = df_tokens_view.set_index("_token_", drop=True)
    if "_ts_" in df_tokens_view.columns:
        df_tokens_view = df_tokens_view.drop(columns=["_ts_"])

    # df for MFF
    df_mff = df_work[df_work["_ts_"].notna()].copy()
    dt_index = pd.DatetimeIndex(df_mff["_ts_"])
    
    # Try to convert DatetimeIndex to PeriodIndex based on inferred frequency
    # This prevents "YS-JAN is not supported" errors from MFF
    try:
        if not dt_index.empty:
            inferred_freq = pd.infer_freq(dt_index)
            if inferred_freq is None:
                # No regular frequency detected - try to infer based on time deltas
                if len(dt_index) >= 2:
                    # Check time differences
                    deltas = dt_index.to_series().diff()
                    median_delta = deltas.median()
                    # Rough frequency detection (in days)
                    days = median_delta.days if hasattr(median_delta, 'days') else median_delta / pd.Timedelta(days=1)
                    if days >= 365:
                        inferred_freq = "YS"
                    elif days >= 80:
                        inferred_freq = "QS"
                    elif days >= 25:
                        inferred_freq = "MS"
                    elif days >= 6:
                        inferred_freq = "W"
                    else:
                        inferred_freq = "D"
            # Convert to PeriodIndex if we have a valid frequency
            if inferred_freq:
                try:
                    freq_char = inferred_freq[0] if len(inferred_freq) > 0 else "D"
                    period_index = dt_index.to_period(freq_char)
                    df_mff.index = period_index
                except Exception:
                    # If period conversion fails, keep DatetimeIndex
                    df_mff.index = dt_index
            else:
                df_mff.index = dt_index
        else:
            df_mff.index = dt_index
    except Exception:
        # Fallback to DatetimeIndex if anything fails
        df_mff.index = dt_index
    
    df_mff = df_mff.drop(columns=["_ts_"] + date_cols, errors="ignore")

    # Preflight checks
    def _check_mff_input(df_mff_local: pd.DataFrame) -> List[str]:
        problems: List[str] = []
        if df_mff_local.empty:
            problems.append("df_mff is empty")
        numeric_cols = [c for c in df_mff_local.columns if pd.api.types.is_numeric_dtype(df_mff_local[c])]
        if not numeric_cols:
            problems.append("no numeric series columns found")
        else:
            if all(df_mff_local[c].notna().sum() < 2 for c in numeric_cols):
                problems.append("no series has >=2 non-null observations")
            # trailing all-NaN horizon
            try:
                is_allna = df_mff_local[numeric_cols].isna().all(axis=1).tolist()
                trailing = 0
                for v in reversed(is_allna):
                    if v:
                        trailing += 1
                    else:
                        break
                if trailing == 0:
                    problems.append("no trailing forecast horizon rows detected")
            except Exception:
                pass
        return problems

    preflight = _check_mff_input(df_mff)
    if preflight:
        raise RuntimeError("MFF preflight checks failed: " + "; ".join(preflight))

    # Determine numeric series and exogenous availability
    numeric_cols = [c for c in df_mff.columns if pd.api.types.is_numeric_dtype(df_mff[c])]
    has_exog = len(numeric_cols) > 1  # more than one series implies exogenous features for some cells

    # Track original forecaster selection for diagnostics
    forecaster_requested = forecaster if isinstance(forecaster, str) else (None if forecaster is None else str(forecaster))

    # Normalize forecaster token for checking
    forecaster_token = forecaster if isinstance(forecaster, str) else (None if forecaster is None else str(forecaster))
    forecaster_token_lower = str(forecaster_token).strip().lower() if forecaster_token else ""
    
    # Determine if user explicitly selected a specific forecaster
    user_selected_specific_forecaster = (
        forecaster_token_lower and 
        forecaster_token_lower not in ("default", "none", "")
    )
    
    # Use DefaultForecaster if no specific forecaster is selected
    # DefaultForecaster will evaluate all models and pick the best one
    if not user_selected_specific_forecaster:
        logger.info("No specific forecaster selected: using DefaultForecaster (ensemble with CV selection)")
        logger.info("DefaultForecaster will evaluate: naive, elastic_net (if multi-series), ols_pca (if multi-series), ols (if multi-series)")
        forecaster = None  # Will be handled by _instantiate_forecaster which returns DefaultForecaster
    else:
        # User selected a specific forecaster - use it
        logger.info("Using user-selected forecaster: %s", forecaster_token_lower)
        forecaster = forecaster_token_lower
    
    # Track forecaster requested before instantiation
    forecaster_actually_used = None  # Will be set after _instantiate_forecaster

    # Classify constraints by operator type (auto-separate mixed constraint lists)
    def _is_inequality_operator(expr_str: str) -> bool:
        """Check if expression contains inequality operators (>=, <=, >, <)"""
        if not expr_str or not isinstance(expr_str, str):
            return False
        expr_str = str(expr_str).strip()
        return any(op in expr_str for op in ('>=', '<=', '>', '<'))

    def _classify_constraints(eq_list: List[str], ineq_list: List[str]) -> Tuple[List[str], List[str]]:
        """Reclassify constraints based on operators, moving inequalities from equality list"""
        true_eq = []
        # NOTE: Current macroframe-forecast v0.1.5 has limited support for inequality constraints
        # So we collect them but they will be handled carefully below
        true_ineq = []  # Start empty - we'll handle inequalities specially
        
        for constraint in (eq_list or []):
            if constraint and isinstance(constraint, str):
                if _is_inequality_operator(constraint):
                    # Move inequality expressions to inequality list
                    true_ineq.append(constraint)
                else:
                    # Keep equality expressions in equality list
                    true_eq.append(constraint)
            elif constraint:
                true_eq.append(constraint)
        
        # Add any provided inequality constraints (they override)
        if ineq_list:
            true_ineq.extend(ineq_list)
        
        return true_eq, true_ineq

    equality_constraints, inequality_constraints = _classify_constraints(
        equality_constraints, inequality_constraints
    )
    logger.info("Reclassified constraints: eq=%d, ineq=%d", 
                len(equality_constraints), len(inequality_constraints))
    
    # NOTE: MFF library v0.1.5 has limited support for inequality constraints
    # They are detected and reclassified correctly, but not passed to MFF
    # Only equality constraints will be enforced in the forecast

    # Normalize constraints
    equality_constraints_safe = [_normalize_constraint_with_freq(c, freq_hint) for c in equality_constraints]
    # Note: inequality_constraints_safe will not be used, but we normalize them for diagnostic purposes
    inequality_constraints_safe = [_normalize_constraint_with_freq(c, freq_hint) for c in inequality_constraints]

    # Monkeypatch wrapper: clean tokens & filter known_cells to non-null only (avoid SymPy float conversion on NaN)
    mff_utils = importlib.import_module("macroframe_forecast.utils")
    _orig_utils_StringToMatrixConstraints = getattr(mff_utils, "StringToMatrixConstraints", None)

    def wrapped_StringToMatrixConstraints(df0_stacked, all_cells, unknown_cells, known_cells, constraints):
        def _clean(val):
            s = str(val or "").strip()
            # Already valid token like SERIES_YYYYQn
            if re.match(r"^[A-Za-z]\w*_\d{4}Q[1-4]$", s) or re.match(r"^[A-Za-z]\w*_\d{4}$", s) or re.match(
                r"^[A-Za-z]\w*_\d{4}M(0[1-9]|1[0-2])$", s
            ):
                return s
            ts = _parse_to_timestamp(s)
            if ts is not None:
                return _timestamp_to_period_token(ts, freq_hint)
            s = s.replace("-", "_").replace("/", "_").replace(":", "_")
            return s

        all_cells_safe = pd.Series([_clean(v) for v in list(all_cells)], index=getattr(all_cells, "index", None))
        unknown_cells_safe = pd.Series([_clean(v) for v in list(unknown_cells)], index=getattr(unknown_cells, "index", None))
        known_cells_safe = pd.Series([_clean(v) for v in list(known_cells)], index=getattr(known_cells, "index", None))

        # Filter known cells to those with actual non-null numeric values
        try:
            known_index = list(known_cells_safe.index)
            known_values = [df0_stacked.loc[idx] for idx in known_index]
            known_mask = [pd.notna(v) and isinstance(float(v), float) and math.isfinite(float(v)) for v in known_values]
            known_cells_filtered = known_cells_safe.iloc[[i for i, ok in enumerate(known_mask) if ok]]
        except Exception:
            known_cells_filtered = known_cells_safe

        return _orig_utils_StringToMatrixConstraints(
            df0_stacked,
            all_cells_safe,
            unknown_cells_safe,
            known_cells_filtered,
            constraints,
        )

    try:
        if _orig_utils_StringToMatrixConstraints is not None:
            mff_utils.StringToMatrixConstraints = wrapped_StringToMatrixConstraints
    except Exception:
        logger.exception("Failed to install StringToMatrixConstraints wrapper")

    # Load MFF
    MFF = getattr(importlib.import_module("macroframe_forecast"), "MFF")

    # Run MFF with short-lived SymPy sanitiser
    import sympy as _sym
    _orig_sympify = getattr(_sym, "sympify", None)

    def _sanitize_token_for_sympy(x):
        try:
            if isinstance(x, pd.Timestamp):
                return _timestamp_to_period_token(x, freq_hint)
        except Exception:
            pass
        s = "" if x is None else str(x)
        if re.search(r"\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}:\d{2}", s):
            s = s.split()[0]
        s = s.replace(":", "_").replace("-", "_").replace("/", "_")
        s = re.sub(r"_+", "_", s).strip("_")
        return s

    def _safe_sympify(a, *args, **kwargs):
        try:
            if isinstance(a, (np.ndarray, list, tuple)):
                cleaned = [_sanitize_token_for_sympy(x) for x in a]
                return _orig_sympify(cleaned, *args, **kwargs)
            if isinstance(a, pd.Series):
                cleaned = [_sanitize_token_for_sympy(x) for x in list(a)]
                return _orig_sympify(cleaned, *args, **kwargs)
        except Exception:
            pass
        return _orig_sympify(a, *args, **kwargs)

    if _orig_sympify is not None:
        _sym.sympify = _safe_sympify

    forecasts = None
    mff_obj = None
    best_model_from_ensemble = None
    cv_scores_from_ensemble = {}
    print(f"DEBUG: About to call MFF.fit() with parallelize={parallelize}...", flush=True)
    try:
        # Instantiate forecaster and capture actual forecaster name (may differ if fallback occurs)
        forecaster_obj, forecaster_actually_used = _instantiate_forecaster(
            forecaster,
            pca_n_components=pca_n_components,
            has_exog=has_exog,
        )
        if forecaster_actually_used is None:
            forecaster_actually_used = forecaster_requested
        
        mff_obj = MFF(
            df=df_mff,
            equality_constraints=equality_constraints_safe,  # Pass normalized equality constraints to MFF
            inequality_constraints=inequality_constraints_safe,  # Pass normalized inequality constraints to MFF
            shrinkage_method=str(shrinkage_method).strip().lower(),
            default_lam=default_lam,
            max_lam=max_lam,
            parallelize=parallelize,
            forecaster=forecaster_obj,
        )
        print("DEBUG: MFF object created, calling fit()...", flush=True)
        print(f"DEBUG: MFF created with {len(equality_constraints_safe)} equality constraints: {equality_constraints_safe}", flush=True)
        forecasts = mff_obj.fit()
        print("DEBUG: MFF.fit() succeeded!", flush=True)
    except Exception as e:
        # Catch any error during MFF forecasting (frequency issues, convergence failures, etc.)
        print(f"DEBUG: MFF.fit() failed with {type(e).__name__}: {str(e)[:200]}", flush=True)
        logger.warning(f"MFF.fit() failed with {type(e).__name__}: {str(e)[:200]}. Using fallback forecasting.")
        # Use simple LOCF fallback with constraints applied
        forecasts = _simple_forecast_fallback(df_mff, eq_constraints=equality_constraints_safe, freq_hint=freq_hint)
        mff_obj = None  # CRITICAL: Set mff_obj to None to trigger fallback reconstruction path
        print("DEBUG: Fallback forecasting completed.", flush=True)
    finally:
        try:
            if _orig_sympify is not None:
                _sym.sympify = _orig_sympify
        except Exception:
            logger.exception("Failed to restore sympy.sympify")

    # Collect results
    # If we used fallback forecasting, mff_obj will be None, so provide defaults
    if forecasts is None:
        raise RuntimeError("Forecasting failed and no fallback was generated")
    
    if mff_obj:
        # Normal MFF path - use MFF's output
        df0 = getattr(mff_obj, "df0", pd.DataFrame())
        df1 = getattr(mff_obj, "df1", pd.DataFrame())
        df2 = getattr(mff_obj, "df2", forecasts if isinstance(forecasts, pd.DataFrame) else pd.DataFrame(forecasts))
        df1_model = getattr(mff_obj, "df1_model", None)
        
        # Add Year column to MFF outputs for Excel compatibility
        # MFF outputs have PeriodIndex, need to convert to timestamps with Year column
        for df_obj in [df0, df1, df2]:
            if df_obj is not None and not df_obj.empty:
                if isinstance(df_obj.index, (pd.DatetimeIndex, pd.PeriodIndex)):
                    if isinstance(df_obj.index, pd.DatetimeIndex):
                        df_obj["Year"] = df_obj.index.strftime("%Y-%m-%d")
                    else:  # PeriodIndex
                        df_obj["Year"] = df_obj.index.to_timestamp().strftime("%Y-%m-%d")
                    # Reorder columns so Year comes first
                    cols = ["Year"] + [c for c in df_obj.columns if c != "Year"]
                    df_obj = df_obj[cols]
        df0 = df0 if df0 is not None else pd.DataFrame()
        df1 = df1 if df1 is not None else pd.DataFrame()
        df2 = df2 if df2 is not None else pd.DataFrame()
    else:
        # Fallback path - reconstruct df0, df1 with Year information
        # df_mff has DatetimeIndex, forecasts has same DatetimeIndex structure
        # We need to add Year column back for Excel compatibility
        
        # Convert forecasts to DataFrame if needed
        if isinstance(forecasts, pd.DataFrame):
            df2 = forecasts.copy()
        else:
            df2 = pd.DataFrame(forecasts)
        
        # Reconstruct df0 (original input data) with Year column
        df_mff_data = df_mff.copy()
        # Handle both DatetimeIndex and PeriodIndex
        if isinstance(df_mff_data.index, (pd.DatetimeIndex, pd.PeriodIndex)):
            if isinstance(df_mff_data.index, pd.DatetimeIndex):
                df_mff_data["Year"] = df_mff_data.index.strftime("%Y-%m-%d")
            else:  # PeriodIndex
                df_mff_data["Year"] = df_mff_data.index.to_timestamp().strftime("%Y-%m-%d")
            # Reorder columns so Year comes first
            cols = ["Year"] + [c for c in df_mff_data.columns if c != "Year"]
            df_mff_data = df_mff_data[cols]
        df0 = df_mff_data.reset_index(drop=True)
        
        # Reconstruct df1 (aligned historical) - same as df0 for simple fallback
        df1 = df0.copy()
        
        # Add Year to df2 (forecasts) if it has DatetimeIndex or PeriodIndex
        if isinstance(df2.index, (pd.DatetimeIndex, pd.PeriodIndex)):
            if isinstance(df2.index, pd.DatetimeIndex):
                df2["Year"] = df2.index.strftime("%Y-%m-%d")
            else:  # PeriodIndex
                df2["Year"] = df2.index.to_timestamp().strftime("%Y-%m-%d")
            # Reorder columns so Year comes first
            cols = ["Year"] + [c for c in df2.columns if c != "Year"]
            df2 = df2[cols]
        
        df1_model = None

    # CRITICAL FIX: Apply constraints to df2 regardless of which path (MFF or fallback) was taken
    # This ensures constraints are always respected in the forecast output
    if equality_constraints_safe and isinstance(df2, pd.DataFrame):
        df2 = _apply_equality_constraints_to_fallback(df2, equality_constraints_safe, freq_hint)
        logger.info(f"Applied {len(equality_constraints_safe)} equality constraints to df2")

    diagnostics: Dict[str, Any] = {
        "constraints_equality": [str(c) for c in equality_constraints_safe],
        "constraints_inequality": [str(c) for c in inequality_constraints],  # Log what was requested
        "note_on_inequalities": "Inequality constraints not yet supported in macroframe-forecast v0.1.5. Only equality constraints are applied.",
        "forecaster_requested": str(forecaster_requested).strip().lower() if forecaster_requested else "default",
        "forecaster_used": str(forecaster_actually_used).strip().lower() if forecaster_actually_used else "default",
        "single_series": len(numeric_cols) == 1,
    }
    
    # Add ensemble information if DefaultForecaster was used
    if best_model_from_ensemble is not None:
        diagnostics["ensemble_best_model"] = best_model_from_ensemble
        diagnostics["ensemble_cv_scores"] = _safe_for_json(cv_scores_from_ensemble)
        logger.info("Added ensemble diagnostics: best_model=%s, cv_scores=%s", best_model_from_ensemble, cv_scores_from_ensemble)
    
    if mff_obj:
        try:
            diagnostics.update({
                "n_eq_constraints": int(getattr(mff_obj, "C", pd.DataFrame()).shape[0]),
                "shrinkage": _safe_for_json(getattr(mff_obj, "shrinkage", None)),
                "lambda_summary": _safe_for_json(getattr(mff_obj, "smoothness", None)),
                "weight_matrix_shape": str(getattr(mff_obj, "W", pd.DataFrame()).shape),
                "smoothing_matrix_shape": str(getattr(mff_obj, "Phi", pd.DataFrame()).shape),
            })
        except Exception:
            pass
    else:
        diagnostics["note"] = "Fallback forecasting used - no MFF diagnostics available"

    return {
        "df0": df0,
        "df1": df1,
        "df2": df2,
        "df1_model": df1_model,
        "diagnostics": _safe_for_json(diagnostics),
    }
