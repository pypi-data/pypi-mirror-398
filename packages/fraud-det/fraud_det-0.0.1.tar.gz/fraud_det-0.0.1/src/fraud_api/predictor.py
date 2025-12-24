from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import joblib
from catboost import CatBoostClassifier

try:
    # Python 3.9+
    from importlib.resources import files as ir_files
except ImportError:
    # Python 3.8 fallback
    from importlib_resources import files as ir_files


ASSETS_DIR = ir_files("fraud_api").joinpath("assets")


def _load_feature_order() -> List[str]:
    p = ASSETS_DIR.joinpath("feature_order.json")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _safe_float(x: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Convert to float safely.
    Returns: (value_or_nan, warning_or_None)
    """
    if x is None:
        return (np.nan, None)
    if isinstance(x, (int, float, np.number)) and not (isinstance(x, float) and np.isnan(x)):
        return (float(x), None)
    if isinstance(x, str):
        s = x.strip().replace(",", ".")
        if s == "":
            return (np.nan, None)
        try:
            return (float(s), None)
        except Exception:
            return (np.nan, f"Could not parse numeric value from '{x}'")
    return (np.nan, f"Unsupported numeric type: {type(x).__name__}")


def _safe_int(x: Any) -> Tuple[Optional[int], Optional[str]]:
    val, warn = _safe_float(x)
    if warn is not None:
        return (np.nan, warn)
    if val is np.nan or (isinstance(val, float) and np.isnan(val)):
        return (np.nan, None)
    try:
        return (int(round(float(val))), None)
    except Exception:
        return (np.nan, f"Could not convert '{x}' to int")


def _safe_str(x: Any) -> Tuple[Optional[str], Optional[str]]:
    if x is None:
        return (None, None)
    if isinstance(x, str):
        s = x.strip()
        return (s if s != "" else None, None)
    # CatBoost accepte souvent des catégories non-string mais on uniformise
    try:
        return (str(x), None)
    except Exception:
        return (None, f"Could not convert value to string: {type(x).__name__}")


@dataclass
class FraudPrediction:
    proba_fraud: float
    proba_raw: float
    warnings: List[str]
    inputs_used: Dict[str, Any]


_model: Optional[CatBoostClassifier] = None
_iso = None
_features: Optional[List[str]] = None


def _lazy_load() -> None:
    global _model, _iso, _features
    if _features is None:
        _features = _load_feature_order()

    if _model is None:
        model_path = ASSETS_DIR.joinpath("catboost.cbm")
        m = CatBoostClassifier()
        m.load_model(str(model_path))
        _model = m

    if _iso is None:
        iso_path = ASSETS_DIR.joinpath("iso_calibrator.pkl")
        _iso = joblib.load(str(iso_path))


def predict_fraud(
    *,
    AccidentArea: Optional[str] = None,
    DayOfWeekClaimed: Optional[str] = None,
    MonthClaimed: Optional[str] = None,
    Sex: Optional[str] = None,
    MaritalStatus: Optional[str] = None,
    Fault: Optional[str] = None,
    VehicleCategory: Optional[str] = None,
    VehiclePrice: Optional[str] = None,
    **kwargs: Any,
) -> FraudPrediction:
    """
    Predict calibrated probability of fraud.

    IMPORTANT:
    - Keyword-only arguments.
    - If a value can't be parsed -> it becomes NaN / None and we return warnings (no crash).

    NOTE:
    - PolicyType is computed automatically as: f"{VehicleCategory} - {BasePolicy}"
      (you should pass BasePolicy below, not PolicyType manually)
    """
    _lazy_load()

    # Full expected features from JSON (source of truth)
    expected = list(_features)  # type: ignore

    warnings: List[str] = []
    inputs: Dict[str, Any] = {}

    # We allow passing extra args via kwargs (but we’ll ignore unknown ones gracefully)
    # We'll read the ones we need from local variables + kwargs.
    provided: Dict[str, Any] = dict(
        AccidentArea=AccidentArea,
        DayOfWeekClaimed=DayOfWeekClaimed,
        MonthClaimed=MonthClaimed,
        Sex=Sex,
        MaritalStatus=MaritalStatus,
        Fault=Fault,
        VehicleCategory=VehicleCategory,
        VehiclePrice=VehiclePrice,
        **kwargs,
    )

    # --- Parse & build inputs ---
    # Categorical features (strings)
    cat_fields = {
        "AccidentArea",
        "DayOfWeekClaimed",
        "MonthClaimed",
        "Sex",
        "MaritalStatus",
        "Fault",
        "VehicleCategory",
        "VehiclePrice",
        "PoliceReportFiled",
        "WitnessPresent",
        "AgentType",
        "AddressChange-Claim",
        "BasePolicy",
        "PolicyType",
        "AgeOfPolicyHolder",
        "NumberOfSuppliments",
        "NumberOfCars",
        "AgeOfVehicle",
        "PastNumberOfClaims",

    }

    # Numeric fields (ints)
    int_fields = {
    }

    # Numeric fields (floats) - in this dataset they’re usually categorical-ish, but safe anyway
    float_fields = {
        "Days:Policy-Accident",
        "Days:Policy-Claim",
    }

    # Fill all expected features, missing -> NaN/None
    for feat in expected:
        raw_val = provided.get(feat, None)

        if feat in cat_fields:
            val, warn = _safe_str(raw_val)
            if warn:
                warnings.append(f"{feat}: {warn}")
            inputs[feat] = val

        elif feat in int_fields:
            val, warn = _safe_int(raw_val)
            if warn:
                warnings.append(f"{feat}: {warn}")
            inputs[feat] = val

        elif feat in float_fields:
            val, warn = _safe_float(raw_val)
            if warn:
                warnings.append(f"{feat}: {warn}")
            inputs[feat] = val

        else:
            # Unknown typing -> store as-is
            inputs[feat] = raw_val

    # Compute PolicyType if expected
    if "PolicyType" in expected:
        vc = inputs.get("VehicleCategory", None)
        bp = inputs.get("BasePolicy", None)
        # Match exactly your training logic: "VehicleCategory - BasePolicy"
        pol = None
        if vc is not None and bp is not None:
            pol = f"{vc} - {bp}"
        inputs["PolicyType"] = pol

    # Build dataframe in correct column order
    row = {c: inputs.get(c, None) for c in expected}
    df = pd.DataFrame([row], columns=expected)
    cat_idx = _model.get_cat_feature_indices()  # indices used at training time
    cat_cols = [expected[i] for i in cat_idx]

    # Replace missing with a safe token and cast to str
    df[cat_cols] = df[cat_cols].where(df[cat_cols].notna(), "__MISSING__").astype(str)


    # Predict
    proba_raw = float(_model.predict_proba(df)[:, 1][0])  # type: ignore
    proba_cal = float(_iso.transform([proba_raw])[0])

    return FraudPrediction(
        proba_fraud=proba_cal,
        proba_raw=proba_raw,
        warnings=warnings,
        inputs_used=row,
    )
