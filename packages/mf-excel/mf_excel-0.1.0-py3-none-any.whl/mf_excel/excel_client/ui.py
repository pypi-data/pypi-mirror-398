# excel_client/ui.py

import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import requests
import xlwings as xw
import numpy as np

from .config import ClientSettings, default_settings_dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _show_error_popup(title: str, message: str, details: Optional[str] = None):
    try:
        import win32com.client  # type: ignore
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.Popup(str(message), 0, str(title), 0x10)
    except Exception:
        logger.error("%s: %s", title, message)
        if details:
            logger.info("%s - details:\n%s", title, details)


def _show_info_popup(title: str, message: str, max_length: int = 1024):
    """Show an info popup with forecast results and diagnostics"""
    try:
        import win32com.client  # type: ignore
        shell = win32com.client.Dispatch("WScript.Shell")
        # Limit message length to avoid popup issues
        msg = str(message)[:max_length]
        if len(message) > max_length:
            msg += f"\n... (truncated, see logs for full details)"
        shell.Popup(msg, 0, str(title), 0x40)  # 0x40 = Information icon
    except Exception:
        logger.info("%s: %s", title, message)



def _format_diagnostics_message(diagnostics: Dict[str, Any]) -> str:
    """Format diagnostics into a user-friendly message"""
    lines = ["Forecast completed successfully!\n"]
    
    # Forecaster info
    forecaster_requested = diagnostics.get("forecaster_requested", "None")
    forecaster_used = diagnostics.get("forecaster_used", "None")
    single_series = diagnostics.get("single_series", False)
    
    if forecaster_requested != forecaster_used:
        lines.append(f"Forecaster Selected: {forecaster_requested}")
        if single_series and forecaster_requested not in ("naive", "None"):
            lines.append(f"  Note: {forecaster_requested} requires multiple series")
            lines.append(f"  (exogenous variables). Single series detected.")
        lines.append(f"  Forecaster Used: {forecaster_used}\n")
    else:
        lines.append(f"Forecaster Used: {forecaster_used}\n")
    
    # Constraints
    eq_constraints = diagnostics.get("constraints_equality", [])
    if eq_constraints:
        lines.append(f"Equality Constraints Applied: {len(eq_constraints)}")
        for i, c in enumerate(eq_constraints[:3], 1):  # Show first 3
            lines.append(f"  {i}. {c}")
        if len(eq_constraints) > 3:
            lines.append(f"  ... and {len(eq_constraints) - 3} more")
    
    # Note on inequalities
    ineq_note = diagnostics.get("note_on_inequalities", "")
    if ineq_note and "not yet supported" not in ineq_note.lower():
        lines.append(f"\nNote: {ineq_note}")
    
    # Shrinkage info
    shrinkage = diagnostics.get("shrinkage", None)
    if shrinkage:
        lines.append(f"\nShrinkage Method: {shrinkage}")
    
    # Lambda info
    lambda_summary = diagnostics.get("lambda_summary", None)
    if lambda_summary:
        lines.append(f"Smoothness: {lambda_summary}")
    
    # Note
    note = diagnostics.get("note", "")
    if note:
        lines.append(f"\nNote: {note}")
    
    return "\n".join(lines)


def _client_preflight_sample(df_records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    sample_rows = df_records[:8]
    sample_brief = []
    for r in sample_rows:
        yr = r.get("Year")
        parsed = None
        try:
            parsed = pd.to_datetime(yr, errors="coerce")
        except Exception:
            parsed = None
        sample_brief.append({"Year_raw": str(yr), "Year_parsed": str(parsed)})
    return sample_brief


def _read_input_table_from_sheet(sheet) -> pd.DataFrame:
    values = sheet.range("A1").expand().value
    if not values or len(values) < 2:
        return pd.DataFrame()
    headers = [str(h).strip() if h is not None else "" for h in values[0]]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    
    # Convert Year column to string to preserve date formats
    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(str)
    
    return df


def _read_constraints_from_sheet(sheet, col_eq: int = 1, col_ineq: int = 2) -> Tuple[List[str], List[str]]:
    used = sheet.used_range
    nrows = used.rows.count
    eq_list: List[str] = []
    ineq_list: List[str] = []
    for r in range(1, nrows + 1):
        try:
            eq_val = sheet.cells(r, col_eq).value
            if eq_val is not None:
                val_str = str(eq_val).strip()
                # Skip header rows and empty values
                if val_str and val_str.lower() not in ("equality constraints", "constraint", "eq", "equality"):
                    eq_list.append(val_str)
        except Exception:
            pass
        try:
            ineq_val = sheet.cells(r, col_ineq).value
            if ineq_val is not None:
                val_str = str(ineq_val).strip()
                # Skip header rows and empty values
                if val_str and val_str.lower() not in ("inequality constraints", "constraint", "ineq", "inequality"):
                    ineq_list.append(val_str)
        except Exception:
            pass
    return eq_list, ineq_list


def write_table_to_sheet(sheet, table: Dict[str, Any], start_cell: str = "A1") -> None:
    logger.info("write_table_to_sheet: table has %d columns, %d data rows", 
                len(table.get("columns", [])), len(table.get("data", [])))
    try:
        sheet.clear()
    except Exception:
        try:
            sheet.used_range.clear()
        except Exception:
            pass
    cols = table.get("columns", [])
    rows = table.get("data", [])
    logger.debug("Writing headers: %s", cols)
    sheet.range(start_cell).value = [cols]
    if rows:
        logger.debug("Writing %d data rows (first row: %s)", len(rows), rows[0] if rows else "")
        # Write data cell-by-cell to ensure Year column is stored as DATE, not as a number
        start_row = 2  # Row after header
        year_col_idx = None
        if "Year" in cols:
            year_col_idx = cols.index("Year")
        
        for row_idx, row in enumerate(rows):
            for col_idx, val in enumerate(row):
                cell = sheet.range(start_row + row_idx, col_idx + 1)
                
                # Format Year column as DATE
                if year_col_idx is not None and col_idx == year_col_idx:
                    # Parse the date string and write as date object so Excel recognizes it as a date
                    try:
                        import datetime
                        if isinstance(val, str):
                            # Parse YYYY-MM-DD format
                            date_parts = val.split('-')
                            if len(date_parts) == 3:
                                cell.value = datetime.datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                            else:
                                cell.value = val
                        else:
                            cell.value = val
                    except Exception:
                        cell.value = val
                    # Set Excel date format: shows as date like "2000-01-01" (no timestamp)
                    cell.number_format = 'YYYY-MM-DD'
                    logger.debug("Year cell A%d formatted as date: %s", start_row + row_idx, val)
                else:
                    # Write numeric values normally
                    cell.value = val
        
    logger.info("write_table_to_sheet: completed successfully")


def write_model_to_sheet(sheet, model_payload: Any, start_cell: str = "A1") -> None:
    logger.info("write_model_to_sheet: payload type=%s", type(model_payload).__name__)
    try:
        sheet.clear()
    except Exception:
        try:
            sheet.used_range.clear()
        except Exception:
            pass
    if model_payload is None:
        logger.info("write_model_to_sheet: payload is None, writing placeholder")
        sheet.range(start_cell).value = [["No model diagnostics available"]]
        return
    if isinstance(model_payload, dict):
        cols = model_payload.get("columns", [])
        data = model_payload.get("data", [])
        idx = model_payload.get("index", [])
        logger.info("write_model_to_sheet: dict format, %d columns, %d rows", len(cols), len(data))
        headers = ["index"] + list(cols)
        sheet.range(start_cell).value = [headers]
        if data:
            combined = [[idx[i]] + row for i, row in enumerate(data)]
            sheet.range(start_cell).offset(1, 0).value = combined
    else:
        logger.info("write_model_to_sheet: writing as string")
        sheet.range(start_cell).value = [[str(model_payload)]]
    logger.info("write_model_to_sheet: completed successfully")


def write_diagnostics_sheet(sheet, diagnostics: Dict[str, Any]) -> None:
    logger.info("write_diagnostics_sheet: %d diagnostic items", len(diagnostics or {}))
    try:
        sheet.clear()
    except Exception:
        try:
            sheet.used_range.clear()
        except Exception:
            pass
    rows: List[List[Any]] = [["key", "value"]]
    for k, v in (diagnostics or {}).items():
        safe_val = "" if v is None else str(v)
        rows.append([str(k), safe_val])
    sheet.range("A1").value = rows
    logger.info("write_diagnostics_sheet: completed successfully")


def _json_safe_df(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    for c in df2.columns:
        try:
            df2[c] = pd.to_numeric(df2[c], errors="ignore")
        except Exception:
            pass
    for c in df2.columns:
        try:
            if pd.api.types.is_numeric_dtype(df2[c]):
                df2[c] = pd.Series(df2[c]).replace([np.inf, -np.inf], np.nan)
        except Exception:
            pass
    return df2.where(pd.notnull(df2), None)


def build_payload(
    df_input: pd.DataFrame,
    eq_constraints: List[str],
    ineq_constraints: List[str],
    forecaster_token: Optional[str] = None,
    shrinkage_method: Optional[str] = None,
    default_lam: Optional[float] = None,
    max_lam: Optional[float] = None,
    parallelize: Optional[bool] = None,
    pca_n_components: Optional[int] = None,
) -> Dict[str, Any]:
    cs = ClientSettings()
    settings = default_settings_dict()

    # Override with user selections from Settings sheet
    if forecaster_token is not None:
        settings["forecaster"] = str(forecaster_token).strip().lower()
    if pca_n_components is not None:
        try:
            settings["pca_n_components"] = int(pca_n_components)
        except Exception:
            settings["pca_n_components"] = None

    df_safe = _json_safe_df(df_input)

    payload: Dict[str, Any] = {
        "data": df_safe.to_dict(orient="records"),
        "equality_constraints": ["" if c is None else str(c) for c in eq_constraints],
        "inequality_constraints": ["" if c is None else str(c) for c in ineq_constraints],
        "settings": settings,
        "shrinkage_method": (shrinkage_method or cs.DEFAULT_SHRINKAGE_METHOD).lower(),
        "default_lam": default_lam if default_lam is not None else cs.DEFAULT_LAMBDA,
        "max_lam": max_lam if max_lam is not None else cs.MAX_LAMBDA,
        "parallelize": bool(parallelize if parallelize is not None else cs.PARALLELIZE),
    }

    try:
        sample = _client_preflight_sample(payload["data"])
        logger.info("Client preflight sample (Year raw/parsed): %s", sample)
    except Exception:
        logger.exception("Failed to produce client preflight sample")
    return payload

def _json_safe_obj(obj):
    import numpy as np
    import pandas as pd
    if obj is None:
        return None
    if isinstance(obj, (str, bool, int, float)):
        try:
            if isinstance(obj, float) and not np.isfinite(obj):
                return None
        except Exception:
            pass
        return obj
    if isinstance(obj, np.generic):
        return _json_safe_obj(obj.item())
    if isinstance(obj, list):
        return [_json_safe_obj(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_json_safe_obj(v) for v in obj)
    if isinstance(obj, dict):
        return {str(k): _json_safe_obj(v) for k, v in obj.items()}
    return str(obj)



def send_forecast(payload: Dict[str, Any], backend_url: Optional[str] = None) -> Dict[str, Any]:
    cs = ClientSettings()
    url = backend_url or cs.BACKEND_URL

    # ✅ Sanitize payload before sending
    safe_payload = _json_safe_obj(payload)

    try:
        resp = requests.post(url + "/forecast", json=safe_payload, timeout=cs.TIMEOUT_SECONDS)

        if resp.status_code != 200:
            try:
                j = resp.json()
                err_msg = j.get("error") or j.get("message") or str(j)
                tb = j.get("traceback") or ""
            except Exception:
                err_msg = f"Forecast request failed (HTTP {resp.status_code})"
                tb = resp.text
            user_message = "Forecast failed - check date formatting and trailing horizon rows."
            details = f"Backend error: {err_msg}\n\nTraceback:\n{tb}"
            _show_error_popup("Macroframe Forecast error", user_message, details)
            raise RuntimeError(details)
        try:
            j = resp.json()
        except Exception as e:
            _show_error_popup("Macroframe Forecast error", "Invalid JSON response from backend.", str(e))
            raise RuntimeError(f"Invalid JSON response: {e}")
        result = j.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("Backend returned an invalid result payload.")
        return result
    except Exception as e:
        _show_error_popup("Macroframe Forecast error", "Unable to run forecast. See logs for details.", str(e))
        raise RuntimeError(f"Forecast request failed: {e}")


def _get_or_add_sheet(wb, name: str):
    try:
        return wb.sheets[name]
    except Exception:
        return wb.sheets.add(name)


def _read_settings_values(wb) -> Tuple[Optional[str], str, float, float, bool, Optional[int]]:
    cs = ClientSettings()
    forecaster_token: Optional[str] = None
    shrinkage_method = cs.DEFAULT_SHRINKAGE_METHOD
    default_lam = cs.DEFAULT_LAMBDA
    max_lam = cs.MAX_LAMBDA
    parallelize = cs.PARALLELIZE
    pca_n_components: Optional[int] = cs.DEFAULT_PCA_N_COMPONENTS

    try:
        sheet = wb.sheets[cs.SHEET_SETTINGS]
        # Settings are stored as: A1="forecaster", B1=value; A2="shrinkage_method", B2=value; etc.
        # Read all values from A:B range
        settings_range = sheet.range("A1:B100").value  # Read up to 100 rows
        
        # Build config dict from the 2-column format
        cfg = {}
        if settings_range:
            for row in settings_range:
                if row and len(row) >= 2:
                    setting_name = row[0]
                    setting_value = row[1]
                    if setting_name:
                        key = str(setting_name).strip().lower()
                        cfg[key] = setting_value
        
        logger.debug("Read settings from Excel: %s", cfg)

        # Forecaster
        if "forecaster" in cfg and cfg["forecaster"] not in (None, "", "None"):
            forecaster_token = str(cfg["forecaster"]).strip().lower()
            logger.info("Forecaster from Settings: %s", forecaster_token)

        # Shrinkage method
        if "shrinkage_method" in cfg and cfg["shrinkage_method"]:
            shrinkage_method = str(cfg["shrinkage_method"]).strip().lower()

        # Default lambda
        if "default_lam" in cfg and cfg["default_lam"] not in (None, ""):
            try:
                default_lam = float(cfg["default_lam"])
            except Exception:
                default_lam = cs.DEFAULT_LAMBDA

        # Max lambda
        if "max_lam" in cfg and cfg["max_lam"] not in (None, ""):
            try:
                max_lam = float(cfg["max_lam"])
            except Exception:
                max_lam = cs.MAX_LAMBDA

        # Parallelize
        if "parallelize" in cfg and cfg["parallelize"] not in (None, ""):
            val = str(cfg["parallelize"]).strip().lower()
            parallelize = val in ("true", "1", "yes")

        # PCA components
        if "pca_n_components" in cfg and cfg["pca_n_components"] not in (None, ""):
            try:
                pca_n_components = int(cfg["pca_n_components"])
            except Exception:
                pca_n_components = None

    except Exception as e:
        # If Settings sheet missing or malformed, fall back to defaults
        logger.warning("Error reading Settings sheet: %s", str(e))
        pass

    return forecaster_token, shrinkage_method, default_lam, max_lam, parallelize, pca_n_components


def run_forecast_ui(wb, backend_url: Optional[str] = None) -> None:
    cs = ClientSettings()
    try:
        sheet_input = wb.sheets[cs.SHEET_INPUT]
    except Exception:
        _show_error_popup("Macroframe Forecast", f"Missing sheet: {cs.SHEET_INPUT}", None)
        return

    df_input = _read_input_table_from_sheet(sheet_input)
    if df_input.empty:
        _show_error_popup("Macroframe Forecast", "Input sheet is empty or invalid.", None)
        return

    try:
        sheet_constraints = wb.sheets[cs.SHEET_CONSTRAINTS]
        eq_list, ineq_list = _read_constraints_from_sheet(
            sheet_constraints, col_eq=cs.CONSTRAINTS_COL_EQ, col_ineq=cs.CONSTRAINTS_COL_INEQ
        )
        if eq_list or ineq_list:
            logger.info("Constraints loaded: %d equality, %d inequality", len(eq_list), len(ineq_list))
            logger.debug("Equality constraints: %s", eq_list)
            logger.debug("Inequality constraints: %s", ineq_list)
    except Exception as e:
        logger.debug("No constraints sheet found or error reading: %s", str(e))
        eq_list, ineq_list = [], []

    # ✅ Read user settings from Settings sheet
    forecaster_token, shrinkage_method, default_lam, max_lam, parallelize, pca_n_components = _read_settings_values(wb)
    
    # Log the settings being used
    logger.info("=" * 60)
    logger.info("FORECAST SETTINGS")
    logger.info("=" * 60)
    logger.info("Forecaster: %s", forecaster_token or "default")
    logger.info("Shrinkage Method: %s", shrinkage_method)
    logger.info("Lambda Range: [%s, %s]", default_lam, max_lam)
    logger.info("Parallelize: %s", parallelize)
    if pca_n_components:
        logger.info("PCA Components: %s", pca_n_components)
    logger.info("Equality Constraints: %d", len(eq_list))
    logger.info("Inequality Constraints: %d", len(ineq_list))
    logger.info("=" * 60)

    # ✅ Build payload with overrides
    payload = build_payload(
        df_input=df_input,
        eq_constraints=eq_list,
        ineq_constraints=ineq_list,
        forecaster_token=forecaster_token,
        shrinkage_method=shrinkage_method,
        default_lam=default_lam,
        max_lam=max_lam,
        parallelize=parallelize,
        pca_n_components=pca_n_components,
    )

    try:
        result = send_forecast(payload, backend_url=backend_url or cs.BACKEND_URL)
        # Flush logger after forecast request completes
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                try:
                    handler.flush()
                except Exception:
                    pass
    except Exception as e:
        logger.exception("Forecast error: %s", e)
        sheet_diag = _get_or_add_sheet(wb, cs.SHEET_DIAGNOSTICS)
        write_diagnostics_sheet(sheet_diag, {"error": str(e)})
        return

    sheet_df0 = _get_or_add_sheet(wb, cs.SHEET_OUTPUT_DF0)
    sheet_df1 = _get_or_add_sheet(wb, cs.SHEET_OUTPUT_DF1)
    sheet_df2 = _get_or_add_sheet(wb, cs.SHEET_OUTPUT_DF2)
    sheet_model = _get_or_add_sheet(wb, cs.SHEET_OUTPUT_MODEL)
    sheet_diag = _get_or_add_sheet(wb, cs.SHEET_DIAGNOSTICS)

    try:
        logger.info("Writing df0 to %s", cs.SHEET_OUTPUT_DF0)
        write_table_to_sheet(sheet_df0, result.get("df0", {"columns": [], "data": []}))
        logger.info("Writing df1 to %s", cs.SHEET_OUTPUT_DF1)
        write_table_to_sheet(sheet_df1, result.get("df1", {"columns": [], "data": []}))
        logger.info("Writing df2 to %s", cs.SHEET_OUTPUT_DF2)
        write_table_to_sheet(sheet_df2, result.get("df2", {"columns": [], "data": []}))
        logger.info("Writing model to %s", cs.SHEET_OUTPUT_MODEL)
        write_model_to_sheet(sheet_model, result.get("df1_model"))
        logger.info("Writing diagnostics to %s", cs.SHEET_DIAGNOSTICS)
        write_diagnostics_sheet(sheet_diag, result.get("diagnostics", {}))
        logger.info("All outputs written successfully")
        
        # Generate charts after all data is written
        logger.info("Generating charts...")
        try:
            insert_charts_ui(wb)
            logger.info("Charts generated successfully")
        except Exception as e:
            logger.exception("Exception generating charts: %s", str(e))
        
        # Show success message with diagnostics
        diagnostics = result.get("diagnostics", {})
        log_message = _format_diagnostics_message(diagnostics)
        
        # Log the popup message content for debugging
        logger.info("=" * 70)
        logger.info("FORECAST COMPLETION SUMMARY")
        logger.info("=" * 70)
        logger.info("Forecaster Requested: %s", diagnostics.get("forecaster_requested", "default"))
        logger.info("Forecaster Used: %s", diagnostics.get("forecaster_used", "default"))
        logger.info("Single Series Data: %s", diagnostics.get("single_series", False))
        logger.info("Equality Constraints Applied: %d", len(diagnostics.get("constraints_equality", [])))
        logger.info("Inequality Constraints: %d", len(diagnostics.get("constraints_inequality", [])))
        logger.info("=" * 70)
        logger.info("Forecast UI popup message:\n%s", log_message)
        logger.info("=" * 70)
        
        _show_info_popup("Macroframe Forecast", log_message)
    except Exception as e:
        logger.exception("Exception writing outputs to Excel: %s", str(e))
        _show_error_popup("Macroframe Forecast", "Failed to write outputs to Excel.", str(e))


def insert_charts_ui(wb) -> None:
    """Insert line charts for forecast data in Output_df2 sheet
    
    Creates separate charts for each data variable (Sales, Cost, etc.)
    with Year as the X-axis (date/category axis) and enables hover/click 
    highlighting of corresponding Year and variable data.
    """
    cs = ClientSettings()
    try:
        sheet = wb.sheets[cs.SHEET_OUTPUT_DF2]
    except Exception:
        logger.warning("Macroframe Forecast: Missing sheet: %s", cs.SHEET_OUTPUT_DF2)
        return

    try:
        # Get data range
        used_range = sheet.used_range
        if used_range.rows.count < 2:
            logger.warning("Macroframe Forecast: No forecast output to chart")
            return
        
        last_row = used_range.rows.count
        last_col = used_range.columns.count
        
        # Get headers
        headers_range = sheet.range(f"A1:{chr(64 + last_col)}1")
        headers_list = headers_range.value
        if not headers_list:
            logger.warning("Macroframe Forecast: Could not read headers")
            return
        
        headers = [str(h).strip() if h else "" for h in headers_list]
        
        if "Year" not in headers:
            logger.warning("Macroframe Forecast: Year column not found in Output_df2")
            return
        
        year_col_idx = headers.index("Year") + 1  # 1-based (A=1, B=2, etc)
        year_col_letter = chr(64 + year_col_idx)  # Convert to letter (A, B, C, etc)
        
        # Get series columns (all except Year)
        series_cols = [i + 1 for i, h in enumerate(headers) if h != "Year"][:cs.CHART_MAX_SERIES]
        
        # Delete existing charts
        try:
            for ch in sheet.charts:
                ch.delete()
        except Exception:
            pass
        
        # Create separate charts for each series variable
        # Each chart plots: Year (X-axis) vs ONE Series Variable (Y-axis)
        # IMPORTANT: Use only Year and one series per chart (not intervening columns)
        chart_row = last_row + 2
        for j, col_idx in enumerate(series_cols):
            series_name = headers[col_idx - 1]
            series_col_letter = chr(64 + col_idx)
            
            try:
                logger.debug("Creating chart '%s': Year (%s) and %s (%s) columns", 
                            series_name, year_col_letter, series_name, series_col_letter)
                
                # Create chart with just the series data (no year initially)
                ch = sheet.charts.add()
                ch.chart_type = "line"
                ch.name = f"{series_name}_Forecast"
                
                # Position charts (2 columns, multiple rows)
                ch.left = 1 + (j % 2) * 400
                ch.top = chart_row + (j // 2) * 250
                
                # Build range strings for Year and series data
                year_range_str = f"${year_col_letter}$1:${year_col_letter}${last_row}"
                series_range_str = f"${series_col_letter}$1:${series_col_letter}${last_row}"
                
                # Get Range objects
                year_range = sheet.range(year_range_str)
                series_range = sheet.range(series_range_str)
                
                try:
                    # Set source data with ONLY the series column (not year)
                    # We'll add Year as XValues via COM API
                    ch.set_source_data(series_range)
                    
                    # Access chart via COM API for configuration
                    chart_obj = ch.api[1]
                    
                    logger.debug("Chart '%s': Added with series range %s",
                               series_name, series_range_str)
                    
                    # Configure the series to use Year as X-axis
                    try:
                        series_collection = chart_obj.SeriesCollection()
                        if series_collection.Count > 0:
                            # Get the first (and only) series
                            active_series = series_collection(1)
                            
                            # Set X-Values to Year column
                            active_series.XValues = year_range.api
                            
                            # Keep Y-Values as is (already set from source data)
                            # active_series.Values is already correct
                            
                            # Set series name
                            active_series.Name = series_name
                            
                            logger.debug("Configured series '%s': XValues=%s, YValues=%s",
                                       series_name, year_range_str, series_range_str)
                    except Exception as series_err:
                        logger.debug("Error configuring series: %s", str(series_err))
                    
                    # Configure axes and title
                    try:
                        # Set chart title
                        chart_obj.HasTitle = True
                        chart_obj.ChartTitle.Text = f"{series_name} Forecast"
                        
                        # Configure X-axis
                        x_axis = chart_obj.Axes(1)
                        x_axis.TickLabelPosition = 4  # xlLow
                        
                        # Configure Y-axis
                        y_axis = chart_obj.Axes(2)
                        y_axis.HasTitle = False
                        
                        logger.info("Created chart '%s': Year (X-axis) vs %s (Y-axis)", 
                                   series_name, series_name)
                    except Exception as config_err:
                        logger.debug("Chart configuration partial: %s", str(config_err))
                        logger.info("Created chart '%s'", series_name)
                        
                except Exception as chart_create_err:
                    logger.warning("Error setting up chart '%s': %s", series_name, str(chart_create_err))
                
            except Exception as e:
                logger.warning("Failed to create chart for series %s: %s", series_name, str(e))
                
    except Exception as e:
        logger.exception("Exception in insert_charts_ui: %s", str(e))


def settings_ui(wb) -> None:
    """
    Ensure a Settings sheet exists with the expected configuration fields,
    and add dropdowns for allowed values.
    """
    cs = ClientSettings()
    try:
        sheet = wb.sheets[cs.SHEET_SETTINGS]
    except Exception:
        sheet = wb.sheets.add(cs.SHEET_SETTINGS)

    try:
        sheet.clear()
    except Exception:
        try:
            sheet.used_range.clear()
        except Exception:
            pass

    rows = [
        ["forecaster", "None"],
        ["shrinkage_method", cs.DEFAULT_SHRINKAGE_METHOD],
        ["default_lam", cs.DEFAULT_LAMBDA],
        ["max_lam", cs.MAX_LAMBDA],
        ["parallelize", "TRUE" if cs.PARALLELIZE else "FALSE"],
        ["pca_n_components", ""],
    ]
    sheet.range("A1").value = rows
    try:
        sheet.range("A1").expand().columns.autofit()
    except Exception:
        pass

    try:
        fore_cell = sheet.range("B1")
        fore_list = "None,naive,elastic_net,ols_pca,ols"
        fore_cell.api.Validation.Delete()
        fore_cell.api.Validation.Add(Type=3, AlertStyle=1, Operator=1, Formula1=fore_list)

        shr_cell = sheet.range("B2")
        shr_list = "oas,oasd,identity,monotone_diagonal"
        shr_cell.api.Validation.Delete()
        shr_cell.api.Validation.Add(Type=3, AlertStyle=1, Operator=1, Formula1=shr_list)

        par_cell = sheet.range("B5")
        par_list = "TRUE,FALSE"
        par_cell.api.Validation.Delete()
        par_cell.api.Validation.Add(Type=3, AlertStyle=1, Operator=1, Formula1=par_list)
    except Exception:
        pass


def view_models_ui(wb) -> None:
    """
    Excel macro entrypoint: activate and display the model diagnostics sheet.
    The model sheet (Output_model) displays model diagnostics from the forecast run.
    """
    cs = ClientSettings()
    try:
        sheet = wb.sheets[cs.SHEET_OUTPUT_MODEL]
        sheet.activate()
    except Exception:
        _show_error_popup(
            "Macroframe Forecast",
            f"Model diagnostics sheet '{cs.SHEET_OUTPUT_MODEL}' not found. Run forecast first.",
            None,
        )