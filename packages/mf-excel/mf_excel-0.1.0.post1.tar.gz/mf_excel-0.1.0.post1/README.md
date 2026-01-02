# mf-excel - An Excel Integration for macroframe-forecast

[![PyPI Version](https://img.shields.io/pypi/v/mf-excel.svg)](https://pypi.org/project/mf-excel/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mf-excel.svg)](https://pypi.org/project/mf-excel/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Kunlex58/mf-excel/blob/main/LICENSE)

mf-excel provides Excel integration functionality for [`macroframe-forecast`](https://pypi.org/project/macroframe-forecast/) Python module developed by [Ando et al., (2025)](https://www.imf.org/en/publications/wp/issues/2025/08/29/a-python-package-to-assist-macroframework-forecasting-concepts-and-examples-570041). See [Github](https://github.com/Kunlex58/mf-excel/tree/main) for more resources.

It allows you to:
- Run constrained macroeconomic forecasts
- Control models and constraints from Excel
- Execute the engine via Flask (local or remote)
- Integrate seamlessly with xlwings

---

## 📦 Installation

Run the following command on the bash CLI.

```bash

pip install mf-excel
```

**Windows Requirement (Important)**

Excel and Python **must have the same bitness**:

| Excel  | Python        |
| ------ | ------------- |
| 64-bit | 64-bit Python |
| 32-bit | 32-bit Python |

Python version 3.12.7 works perfect for the package. A virtual environment can be created on VS Code IDE.

## 📊 Excel Integration (xlwings)

**Install xlwings**

On the bash CLI, run the following code.

```bash

pip install xlwings
```

**Load the xlwings Add-in**

1. Open Excel
2. Go to **Developer → Excel Add-ins → Browse**
3. Select `xlwings.xlam`
4. Restart Excel if prompted

## Point the Python Interpreter and Work directory PATH to the xlwings

1. Reopen Excel
2. Click on the xlwings menu
3. Locate the *Interpreter* space and paste the Python PATH e.g. `(C:\Users\macro\Desktop\mf_excel\.venv\Scripts\python.exe)`.
4. Locate the *PYTHONPATH* space and paste the PATH where the excel_client folder in the mf_excel package is located e.g `(C:\Users\macro\Desktop\mf_excel_test\.venv\Lib\site-packages\mf_excel)`.
5. Save the Excel file as Macro-Enabled Worksheet (.xlsm)


## Running the Forecast Backend
The backend is a Flask application that Excel communicates with over HTTP.


**Run from VS Code and Jupyter Notebook (Recommended)**

This is the safest way to run Flask alongside Excel. Create a Jupyter Notebook file in your workspace on VS Code, select the virtual environment in your workspace as your Python interpreter, and paste and run the following code.

```python

from mf_excel.backend.app import app
from mf_excel.backend.services.config import settings
import threading

def start_flask():
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=False,
        use_reloader=False
    )

threading.Thread(target=start_flask, daemon=True).start()

print("MacroFrame Forecast backend running")
```

⚠️ Always use use_reloader=False on Windows.

## 📊 Excel Workbook Structure

Your Excel workbook should contain the following sheets:

| Sheet Name  | Purpose                                                        |
| ----------- | -------------------------------------------------------------- |
| Input       | Time series data                                               |
| Control     | Run Forecast, View Models, Insert Charts, and Settings Buttons |


## VBA Button Wiring

Create a VBA module in Excel (Alt + F11 → Insert → Module) and paste the following:

```vb

Sub RunMacroFrameForecast()
    RunPython "import macroframe_excel.excel_client.addin as a; a.run_forecast_button()"
End Sub

Sub InsertMacroFrameCharts()
    RunPython "import macroframe_excel.excel_client.addin as a; a.insert_charts_button()"
End Sub

Sub ViewMacroFrameModels()
    RunPython "import macroframe_excel.excel_client.addin as a; a.view_models_button()"
End Sub

Sub OpenMacroFrameSettings()
    RunPython "import macroframe_excel.excel_client.addin as a; a.settings_button()"
End Sub
```

## Assigning Buttons in Excel Control Sheet

1. Go to Insert → Shapes
2. Draw a button and assign appropriate names (e.g., Run Forecast or View Models)
3. Right-click → Assign Macro
4. Choose one of:
   - `RunMacroFrameForecast` (for Run Forecast Button)
   - `InsertMacroFrameCharts` (for Insert Charts Button)
   - `ViewMacroFrameModels` (for View Models Button)
   - `OpenMacroFrameSettings` (for Settings Button)

Note: The control sheet should have 4 buttons (Run Forecast, View Models, Insert Charts, Settings). 

## Input Data Format

Forecast input data must be in tabular form. See the example datasets 'test.csv' and 'test2.csv' on the Github. 

Example:

| Year | GDP  |
|------|------|
| 1960 | 0.54 |
| 1961 | 0.56 |
| 1962 | 0.60 |
| 1963 | 0.64 |
| 1964 | 0.69 |
| 1965 | 0.74 |
| 1966 | 0.81 |
| 1967 | 0.86 |
| 1968 | 0.94 |
| 1969 | 1.02 |
| ...  | ...  |
| 2024 | 29.2 |
| 2025 |      |
| 2026 |      |
| 2027 |      |
| 2028 |      |
| 2029 |      |
| 2030 |      |


Rules:

- Time column must be one of: Year, Quarter, Month, Week, Day
- Leave forecast horizon rows blank
- Each variable must be numeric

## Constraints

Input the constraints in the *Constraints* sheet. Constraints are optional and entered as expressions.

**Examples**

```makefile

GDP_2030 = 1.04 * GDP_2029

```
These constraints are:

- Validated before model execution
- Applied during forecast optimization
- Compatible with Excel UI inputs

## Making Forecast

1. With the backend already running, click the 'Settings' Button in the *Control* sheet. It will add a new sheet named 'Settings' in the Excel.
2. Click on the *Settings* sheet and specify the forecaster model and parameters to use in your forecast. You must be familiar with the original work of Ando et al., (2025) to understand the process.
3. After selecting forecaster and parameters, return to the *Control* sheet and click 'Run Forecast' Button. It will return the outputs and diagnostics in separate sheets after a few seconds or minutes depending on the model selected.


## License
MIT License - See [LICENSE](https://github.com/Kunlex58/mf-excel/blob/main/LICENSE) for details.

## Support Notes

- Always start the backend before clicking Excel buttons
- Do not run Flask in debug mode on Windows
- Ensure Python and Excel bitness match
- Use Jupyter Notebook or VS Code for interactive workflows

## Next Steps 🗺️

We will continue to monitor updates to the `macroframe-forecast` package. 

## References

Ando Sakai, Shuvam Das, and Sultan Orazbayev (2025). "A Python Package to Assist Macroframework Forecasting: Concepts and Examples", IMF Working Papers 2025, 172, accessed 28/12/2025, https://doi.org/10.5089/9798229023535.001
