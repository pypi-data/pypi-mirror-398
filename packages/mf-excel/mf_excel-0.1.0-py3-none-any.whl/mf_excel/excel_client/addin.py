# excel_client/addin.py
import logging
from typing import Optional
import xlwings as xw

from .config import ClientSettings
from .ui import (
    _show_error_popup,
    run_forecast_ui,
    insert_charts_ui,
    settings_ui,
    view_models_ui,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _active_workbook() -> Optional[xw.Book]:
    try:
        return xw.apps.active.books.active
    except Exception:
        return None


def _write_diagnostics_from_error(wb: xw.Book, error_text: str):
    """
    Write an error message to the Diagnostics sheet to aid troubleshooting.
    """
    cs = ClientSettings()
    try:
        sheet_diag = wb.sheets[cs.SHEET_DIAGNOSTICS]
    except Exception:
        sheet_diag = wb.sheets.add(cs.SHEET_DIAGNOSTICS)
    try:
        sheet_diag.clear()
    except Exception:
        try:
            sheet_diag.used_range.clear()
        except Exception:
            pass
    sheet_diag.range("A1").value = [["error"], [str(error_text)]]


def run_forecast_button():
    """
    Excel macro entrypoint: run forecast and write outputs.
    """
    wb = _active_workbook()
    if wb is None:
        _show_error_popup("Macroframe Forecast", "No active workbook found.", None)
        return
    try:
        cs = ClientSettings()
        run_forecast_ui(wb, backend_url=cs.BACKEND_URL)
    except Exception as e:
        _show_error_popup("Macroframe Forecast", "Unexpected error running forecast.", str(e))
        _write_diagnostics_from_error(wb, str(e))


def insert_charts_button():
    """
    Excel macro entrypoint: insert charts on forecast output sheet.
    """
    wb = _active_workbook()
    if wb is None:
        _show_error_popup("Macroframe Forecast", "No active workbook found.", None)
        return
    try:
        insert_charts_ui(wb)
    except Exception as e:
        _show_error_popup("Macroframe Forecast", "Unexpected error inserting charts.", str(e))


def view_models_button():
    """
    Excel macro entrypoint: activate the model diagnostics sheet.
    """
    wb = _active_workbook()
    if wb is None:
        _show_error_popup("Macroframe Forecast", "No active workbook found.", None)
        return
    try:
        view_models_ui(wb)
    except Exception as e:
        _show_error_popup("Macroframe Forecast", "Unexpected error opening model diagnostics.", str(e))


def settings_button():
    """
    Excel macro entrypoint: initialise or refresh the Settings sheet.
    """
    wb = _active_workbook()
    if wb is None:
        _show_error_popup("Macroframe Forecast", "No active workbook found.", None)
        return
    try:
        settings_ui(wb)
    except Exception as e:
        _show_error_popup("Macroframe Forecast", "Unexpected error creating Settings.", str(e))


def main():
    run_forecast_button()
