# backend/app.py
import sys
import os

from flask import Flask, request, jsonify
import math
import pandas as pd
import numpy as np
import traceback
import logging
from typing import Any, Dict
import warnings

from mf_excel.backend.services.config import settings
from mf_excel.backend.services.validation import validate_payload
from mf_excel.backend.services.forecast_service import (
    run_forecast,
    _safe_for_json,
)

warnings.filterwarnings("ignore", category=FutureWarning)

# Configure root logger for console output
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Remove any existing handlers to avoid duplicates
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)


# Create a custom formatter that forces flush
class FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)


# Add console handler with DEBUG level and auto-flush
sh = FlushingStreamHandler(stream=sys.stdout)
sh.setLevel(logging.DEBUG)
fmt = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s", datefmt="%H:%M:%S"
)
sh.setFormatter(fmt)
root_logger.addHandler(sh)

# Also add stderr handler for critical messages
sh_err = FlushingStreamHandler(stream=sys.stderr)
sh_err.setLevel(logging.WARNING)
fmt_err = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s", datefmt="%H:%M:%S"
)
sh_err.setFormatter(fmt_err)
root_logger.addHandler(sh_err)

logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify(
        {"status": "ok", "message": "MacroFrame Forecast service is running"}
    )


def _ensure_df_finite(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    for c in df2.columns:
        if pd.api.types.is_numeric_dtype(df2[c]):
            df2[c] = df2[c].replace([np.inf, -np.inf], np.nan)
    return df2


def _to_python_native(x: Any) -> Any:
    import numpy as _np
    import pandas as _pd
    import datetime as _datetime

    if x is None:
        return None
    try:
        if x is _pd.NA:
            return None
    except Exception:
        pass
    try:
        if isinstance(x, _pd.Timestamp):
            return x.strftime("%Y-%m-%d")  # Return clean date format without time
    except Exception:
        pass
    try:
        if isinstance(x, _datetime.date):
            return x.strftime(
                "%Y-%m-%d"
            )  # Return clean date format for datetime.date objects
    except Exception:
        pass
    try:
        if isinstance(x, _np.generic):
            try:
                py = x.item()
            except Exception:
                py = x.tolist()
            return _to_python_native(py)
    except Exception:
        pass
    if isinstance(x, float):
        if math.isnan(x) or not math.isfinite(x):
            return None
    if isinstance(x, (str, int, bool)):
        return x
    if isinstance(x, dict):
        return {str(k): _to_python_native(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_to_python_native(v) for v in x]
    try:
        return str(x)
    except Exception:
        return None


def _df_payload(df_any: pd.DataFrame) -> Dict[str, Any]:
    rows = []
    for _, row in df_any.reset_index(drop=True).iterrows():
        rows.append([_to_python_native(v) for v in row.tolist()])
    return {"columns": [str(c) for c in df_any.columns.tolist()], "data": rows}


def _sanitize_for_json(obj: Any) -> Any:
    return _safe_for_json(obj)  # reuse the same sanitiser


def _log_nonfinite_in_df(name: str, df: pd.DataFrame) -> None:
    try:
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                col = df[c]
                inf_mask = np.isinf(col.values.astype("float64", copy=False))
                nan_mask = pd.isna(col)
                if inf_mask.any() or nan_mask.any():
                    n_inf = int(inf_mask.sum())
                    n_nan = int(nan_mask.sum())
                    logger.warning(
                        "DataFrame %s column %s has %d Inf and %d NaN values",
                        name,
                        c,
                        n_inf,
                        n_nan,
                    )
    except Exception:
        logger.exception("Failed to inspect non-finite values in DataFrame %s", name)


@app.route("/forecast", methods=["POST"])
def forecast_endpoint():
    # Optional: Write debug file to Windows temp directory
    try:
        import tempfile

        debug_file = os.path.join(tempfile.gettempdir(), "flask_debug.txt")
        with open(debug_file, "a") as f:
            f.write("DEBUG: forecast_endpoint called\n")
    except Exception:
        pass
    try:
        payload = request.get_json()
        logger.debug(
            "Incoming forecast payload: %s",
            payload if isinstance(payload, dict) else str(payload),
        )

        validation = validate_payload(payload)
        if isinstance(validation, dict) and not validation.get("ok", False):
            error_payload = {"status": "error", "errors": validation.get("errors", [])}
            logger.info("Payload validation failed: %s", validation.get("errors", []))
            return jsonify(_sanitize_for_json(error_payload)), 400

        data_raw = (
            payload.get("data")
            if payload.get("data") is not None
            else payload.get("df")
        )
        if data_raw is None:
            raise ValueError("Missing required field 'data' or 'df' in payload")

        data = pd.DataFrame.from_records(data_raw)
        logger.info("Input DataFrame shape: %s", data.shape)
        logger.debug("Input DataFrame head:\n%s", data.head().to_string())

        _log_nonfinite_in_df("input (raw)", data)

        for c in data.columns:
            try:
                data[c] = pd.to_numeric(data[c], errors="ignore")
            except Exception:
                pass
        for c in data.columns:
            try:
                if pd.api.types.is_numeric_dtype(data[c]):
                    data[c] = pd.Series(data[c]).replace([np.inf, -np.inf], np.nan)
            except Exception:
                pass

        user_settings = payload.get("settings", {}) or {}
        forecaster_token = user_settings.get("forecaster", None)

        # Convert "None" string to actual None to use MFF's DefaultForecaster
        if isinstance(forecaster_token, str) and forecaster_token.lower() in (
            "none",
            "",
        ):
            forecaster_token = None

        pca_n_components = user_settings.get(
            "pca_n_components", settings.forecast_settings.get("pca_n_components", None)
        )

        # Convert parallelize string to boolean
        parallelize_val = payload.get(
            "parallelize", settings.forecast_settings["parallelize"]
        )
        if isinstance(parallelize_val, str):
            parallelize = parallelize_val.lower() in ("true", "1", "yes")
        else:
            parallelize = bool(parallelize_val)

        logger.info(
            "Calling run_forecast with forecaster=%s pca_n_components=%s parallelize=%s",
            forecaster_token,
            pca_n_components,
            parallelize,
        )
        result = run_forecast(
            df=data,
            equality_constraints=payload.get("equality_constraints", []),
            inequality_constraints=payload.get("inequality_constraints", []),
            shrinkage_method=payload.get(
                "shrinkage_method",
                settings.forecast_settings["default_shrinkage_method"],
            ).lower(),
            default_lam=payload.get(
                "default_lam", settings.forecast_settings["default_lambda"]
            ),
            max_lam=payload.get("max_lam", settings.forecast_settings["max_lambda"]),
            parallelize=parallelize,
            forecaster=forecaster_token,
            horizon_override=None,
            pca_n_components=pca_n_components,
        )
        if not result:
            raise ValueError("No forecast results returned")

        df0 = _ensure_df_finite(result["df0"].copy())
        df1 = _ensure_df_finite(result["df1"].copy())
        df2 = _ensure_df_finite(result["df2"].copy())
        df1_model = result.get("df1_model", None)
        diagnostics = result.get("diagnostics", {})

        _log_nonfinite_in_df("df0 (result)", df0)
        _log_nonfinite_in_df("df1 (result)", df1)
        _log_nonfinite_in_df("df2 (result)", df2)

        logger.debug("Diagnostics before sanitise: %s", diagnostics)

        # Format and reorder columns in each dataframe
        for i, frame in enumerate([df0, df1, df2]):
            frame_name = ["df0", "df1", "df2"][i]
            if "Year" in frame.columns:
                try:
                    # Convert Year to datetime (DATE format) so it's recognized as dates, not numbers
                    # Strip time component to return just the date (YYYY-MM-DD)
                    # This ensures charts will plot Year on X-axis as a date axis without timestamp
                    logger.debug(
                        "Converting %s Year column to datetime: %s",
                        frame_name,
                        frame["Year"].tolist()[:3],
                    )
                    frame["Year"] = pd.to_datetime(
                        frame["Year"], errors="coerce"
                    ).dt.date
                    logger.debug(
                        "Converted %s Year to datetime: %s",
                        frame_name,
                        frame["Year"].tolist()[:3],
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to convert %s Year to datetime: %s", frame_name, str(e)
                    )
                    frame["Year"] = frame["Year"].astype(str)
            # Ensure Year column comes first if it exists
            if "Year" in frame.columns:
                cols = ["Year"] + [c for c in frame.columns if c != "Year"]
                frame = frame[cols]
                # Update the variables
                if i == 0:
                    df0 = frame
                elif i == 1:
                    df1 = frame
                else:
                    df2 = frame

        df0_payload = _df_payload(df0)
        df1_payload = _df_payload(df1)
        df2_payload = _df_payload(df2)

        if df1_model is not None and isinstance(df1_model, pd.DataFrame):
            df1_model = _ensure_df_finite(df1_model)
            _log_nonfinite_in_df("df1_model (result)", df1_model)
            df1_model_payload = {
                "columns": [str(c) for c in df1_model.columns.tolist()],
                "data": [
                    [_to_python_native(v) for v in row.tolist()]
                    for _, row in df1_model.reset_index(drop=True).iterrows()
                ],
                "index": [_to_python_native(i) for i in df1_model.index.tolist()],
            }
        else:
            df1_model_payload = str(df1_model) if df1_model is not None else None

        logger.info("Preparing result payload; will sanitize before returning.")
        logger.debug("Diagnostics (raw): %s", diagnostics)

        result_payload = {
            "df0": df0_payload,
            "df1": df1_payload,
            "df2": df2_payload,
            "df1_model": df1_model_payload,
            "diagnostics": _safe_for_json(diagnostics),
        }
        result_payload = _sanitize_for_json(result_payload)
        logger.debug("Result payload sanitized; returning to client.")

        # Flush logging to ensure output is visible in bash terminal when called from Excel
        for handler in logger.handlers:
            if hasattr(handler, "flush"):
                try:
                    handler.flush()
                except Exception:
                    pass

        return jsonify({"result": result_payload})

    except Exception as e:
        logger.error("Exception in /forecast handler: %s", str(e))
        logger.error(traceback.format_exc())
        error_payload = {"error": str(e), "traceback": traceback.format_exc()}
        error_payload = _sanitize_for_json(error_payload)
        logger.debug("Returning error payload (sanitized).")

        # Flush logging to ensure output is visible in bash terminal
        for handler in logger.handlers:
            if hasattr(handler, "flush"):
                try:
                    handler.flush()
                except Exception:
                    pass

        return jsonify(error_payload), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
