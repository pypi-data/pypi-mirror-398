# backend/services/config.py
import os
from typing import Optional


def _env_int(name: str, default: Optional[int]) -> Optional[int]:
    val = os.getenv(name, "")
    if val == "":
        return default
    try:
        return int(val)
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


class Settings:
    # Server configuration
    HOST = os.getenv("FORECAST_HOST", "127.0.0.1")
    PORT = int(os.getenv("FORECAST_PORT", "5001"))
    DEBUG = os.getenv("FORECAST_DEBUG", "false").lower() == "true"

    # Default forecast settings (align with excel_client/config.py)
    forecast_settings = {
        "default_shrinkage_method": os.getenv("FORECAST_SHRINKAGE", "OAS"),
        "default_forecaster": os.getenv("FORECAST_FORECASTER", None),  # None uses macroframe-forecast's DefaultForecaster (sktime ensemble with CV)
        # pca_n_components is optional; None means "user-defined only"
        "pca_n_components": _env_int("FORECAST_PCA_N_COMPONENTS", None),
        "default_lambda": _env_float("FORECAST_DEFAULT_LAMBDA", -1.0),
        "max_lambda": _env_float("FORECAST_MAX_LAMBDA", 129600.0),
        "parallelize": os.getenv("FORECAST_PARALLELIZE", "true").lower() == "true",  # Enable by default - use Dask for distributed computing
    }


settings = Settings()
