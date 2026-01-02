# excel_client/config.py (only small fix)
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ClientSettings:
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 5001
    TIMEOUT_SECONDS: int = 1200  # 20 minutes for long-running MFF computations

    DEFAULT_SHRINKAGE_METHOD: str = "oas"
    DEFAULT_FORECASTER: Optional[str] = None  # None uses macroframe-forecast's DefaultForecaster (sktime ensemble with CV)
    DEFAULT_PCA_N_COMPONENTS: Optional[int] = None
    DEFAULT_LAMBDA: float = -1.0
    MAX_LAMBDA: float = 129600.0
    PARALLELIZE: bool = True  # Enable by default - use Dask for distributed computing

    SHEET_INPUT: str = "Input"
    SHEET_CONSTRAINTS: str = "Constraints"
    SHEET_SETTINGS: str = "Settings"
    SHEET_OUTPUT_DF0: str = "Output_df0"
    SHEET_OUTPUT_DF1: str = "Output_df1"
    SHEET_OUTPUT_DF2: str = "Output_df2"
    SHEET_OUTPUT_MODEL: str = "Output_model"
    SHEET_DIAGNOSTICS: str = "Diagnostics"

    CONSTRAINTS_COL_EQ: int = 1
    CONSTRAINTS_COL_INEQ: int = 2

    CHART_SHEETS: List[str] = field(default_factory=lambda: ["Output_df2"])
    CHART_MAX_SERIES: int = 6

    @property
    def BACKEND_URL(self) -> str:
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"

def default_settings_dict() -> Dict[str, object]:
    cs = ClientSettings()
    payload = {"forecaster": cs.DEFAULT_FORECASTER}
    if cs.DEFAULT_PCA_N_COMPONENTS is not None:
        payload["pca_n_components"] = cs.DEFAULT_PCA_N_COMPONENTS
    return payload
