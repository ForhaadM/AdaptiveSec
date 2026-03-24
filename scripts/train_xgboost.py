"""
train_xgboost.py
================
AdaptiveSec — XGBoost Risk Scoring Model Training Script

What this script does:
    1. Loads PhiUSIIL (~235k rows) from data/raw/phiusiil/  — primary training set
    2. Loads Kaggle 10k dataset from data/raw/kaggle/        — cross-validation set
    3. Maps both datasets onto AdaptiveSec's 8-feature schema (F1–F8)
    4. Synthetically injects F6, F7, F8 (behavioral columns not in either dataset)
    5. Trains XGBoost on PhiUSIIL (80/20 internal split)
    6. Cross-validates on the Kaggle 10k to confirm generalization
    7. Saves the trained model artifact to models/xgboost_risk_model.json

Dataset layout expected:
    data/raw/phiusiil/   <- drop your PhiUSIIL CSV here (any filename works)
    data/raw/kaggle/     <- drop your Kaggle 10k CSV here (any filename works)

Run from the project root:
    python scripts/train_xgboost.py

Requirements:
    pip install xgboost scikit-learn pandas numpy
"""

import os
import sys
import glob
import logging
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths — all relative to project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHIUSIIL_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "phiusiil")
KAGGLE_DIR   = os.path.join(PROJECT_ROOT, "data", "raw", "kaggle")
MODEL_DIR    = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH   = os.path.join(MODEL_DIR, "xgboost_risk_model.json")

os.makedirs(MODEL_DIR, exist_ok=True)


# ===========================================================================
# STEP 1 — Load Datasets
# ===========================================================================

def find_csv(directory: str, label: str) -> str:
    """
    Find the first CSV in a directory — filename doesn't matter.
    Exits with a clear message if the folder or CSV is missing.
    """
    if not os.path.isdir(directory):
        log.error("Directory not found: %s", directory)
        log.error("Create the folder and drop your %s CSV inside it.", label)
        sys.exit(1)

    csvs = glob.glob(os.path.join(directory, "*.csv"))
    if not csvs:
        log.error("No CSV found in: %s", directory)
        log.error("Drop your %s CSV into that folder and re-run.", label)
        sys.exit(1)

    if len(csvs) > 1:
        log.warning("Multiple CSVs in %s — using: %s", directory, os.path.basename(csvs[0]))

    return csvs[0]


def load_phiusiil() -> pd.DataFrame:
    path = find_csv(PHIUSIIL_DIR, "PhiUSIIL")
    log.info("Loading PhiUSIIL from: %s", os.path.basename(path))
    df = pd.read_csv(path)
    log.info("  Loaded %d rows, %d columns", len(df), len(df.columns))
    return df


def load_kaggle() -> pd.DataFrame:
    path = find_csv(KAGGLE_DIR, "Kaggle 10k")
    log.info("Loading Kaggle 10k from: %s", os.path.basename(path))
    df = pd.read_csv(path)
    log.info("  Loaded %d rows, %d columns", len(df), len(df.columns))
    return df


# ===========================================================================
# STEP 2 — Map columns to AdaptiveSec F1-F8 schema
# ===========================================================================

def build_feature_matrix(
    df: pd.DataFrame,
    dataset_name: str,
    rng: np.random.Generator,
) -> tuple:
    """
    Map a raw dataset onto the 8 AdaptiveSec features.
    Handles both PhiUSIIL (46 columns) and Kaggle (31 columns) by checking
    which columns are present and falling back gracefully for each.

    DDD Feature Index Map (Section 4.2.B):
        F1 [0] url_length               <- URLLength (PhiUSIIL direct)
        F2 [1] num_subdomains           <- NoOfSubDomain (PhiUSIIL)
                                           having_Sub_Domain (Kaggle, -1/0/1 scale)
        F3 [2] has_suspicious_keywords  <- Engineered from obfuscation signals
        F4 [3] contains_ip_address      <- IsDomainIP (PhiUSIIL)
                                           having_IP_Address (Kaggle)
        F5 [4] is_https                 <- IsHTTPS (PhiUSIIL)
                                           HTTPS_token (Kaggle)
        F6 [5] time_of_day_encoded      <- SYNTHETIC (neither dataset has this)
        F7 [6] session_fatigue_index    <- SYNTHETIC (neither dataset has this)
        F8 [7] trigger_type_encoded     <- SYNTHETIC (neither dataset has this)
    """
    log.info("Building F1-F8 feature matrix for: %s", dataset_name)
    n    = len(df)
    cols = set(df.columns)

    # F1 — url_length
    if "URLLength" in cols:
        f1 = df["URLLength"].astype(float)
    elif "url" in cols or "URL" in cols:
        url_col = "url" if "url" in cols else "URL"
        f1 = df[url_col].astype(str).str.len().astype(float)
    else:
        length_col = next((c for c in cols if "length" in c.lower()), None)
        if length_col:
            f1 = df[length_col].map({-1: 20.0, 0: 40.0, 1: 75.0}).fillna(40.0)
        else:
            f1 = pd.Series(np.full(n, 40.0))
    log.info("  F1 url_length       — OK (mean=%.1f)", f1.mean())

    # F2 — num_subdomains
    if "NoOfSubDomain" in cols:
        f2 = df["NoOfSubDomain"].astype(float)
    elif "having_Sub_Domain" in cols:
        f2 = df["having_Sub_Domain"].map({-1: 0.0, 0: 1.0, 1: 3.0}).fillna(0.0)
    else:
        f2 = pd.Series(np.zeros(n))
    log.info("  F2 num_subdomains   — OK (mean=%.2f)", f2.mean())

    # F3 — has_suspicious_keywords (engineered binary)
    # Scans across all known column names from both dataset versions.
    suspicious_signals = []
    # PhiUSIIL signals
    if "IsHTTPS" in cols:
        suspicious_signals.append(df["IsHTTPS"] == 0)
    if "HasObfus" in cols:
        suspicious_signals.append(df["HasObfus"] == 1)
    if "NoOfAtSymbol" in cols:
        suspicious_signals.append(df["NoOfAtSymbol"] > 0)
    # PhiUSIIL extended columns (56-col variant)
    if "NoOfOtherSpecialCharsInURL" in cols:
        suspicious_signals.append(df["NoOfOtherSpecialCharsInURL"] > 2)
    if "IsHTTPS" not in cols:
        http_col = next((c for c in cols if "http" in c.lower()), None)
        if http_col:
            suspicious_signals.append(df[http_col] == 0)
    # Kaggle signals
    if "having_At_Symbol" in cols:
        suspicious_signals.append(df["having_At_Symbol"] == 1)
    if "Prefix_Suffix" in cols:
        suspicious_signals.append(df["Prefix_Suffix"] == -1)
    if "having_Dash_Redirect" in cols:
        suspicious_signals.append(df["having_Dash_Redirect"] == 1)

    if suspicious_signals:
        combined = suspicious_signals[0]
        for sig in suspicious_signals[1:]:
            combined = combined | sig
        f3 = combined.astype(float)
    else:
        # Last resort: derive from label — phishing rows have a base signal rate
        log.warning("  F3: no structural columns found, using label-based estimate.")
        f3 = label_col.astype(float) * 0.0  # will be recalculated below
        f3 = pd.Series(np.zeros(n))
    log.info("  F3 suspicious_kw    — OK (positive rate=%.1f%%)", f3.mean() * 100)

    # F4 — contains_ip_address
    if "IsDomainIP" in cols:
        f4 = df["IsDomainIP"].astype(float)
    elif "having_IP_Address" in cols:
        f4 = (df["having_IP_Address"] == 1).astype(float)
    else:
        f4 = pd.Series(np.zeros(n))
    log.info("  F4 contains_ip      — OK (positive rate=%.1f%%)", f4.mean() * 100)

    # F5 — is_https
    if "IsHTTPS" in cols:
        f5 = df["IsHTTPS"].astype(float)
    elif "HTTPS_token" in cols:
        f5 = (df["HTTPS_token"] != -1).astype(float)
    else:
        f5 = pd.Series(np.ones(n))
    log.info("  F5 is_https         — OK (positive rate=%.1f%%)", f5.mean() * 100)

    # F6 — time_of_day (SYNTHETIC)
    f6 = pd.Series(rng.choice([0.0, 1.0, 2.0], size=n, p=[0.40, 0.35, 0.25]))
    log.info("  F6 time_of_day      — SYNTHETIC injection OK")

    # F7 — session_fatigue (SYNTHETIC — Beta distribution)
    f7 = pd.Series(np.clip(rng.beta(a=2, b=3, size=n), 0.0, 1.0))
    log.info("  F7 session_fatigue  — SYNTHETIC injection OK (mean=%.2f)", f7.mean())

    # F8 — trigger_type (SYNTHETIC — assigned to ALL rows to prevent data leakage)
    # Previously only phishing rows got non-zero values, which caused F8 to become
    # a near-perfect proxy for the label (81% importance). Fix: assign trigger types
    # randomly to all rows using realistic base rates from social engineering research.
    # This forces the model to learn from structural URL features (F1-F5) instead.
    #
    # Distribution: ~60% of all URLs have no trigger (0), the rest are distributed
    # across the 4 cognitive trigger types weighted toward Urgency.
    label_col = _resolve_label(df, dataset_name)
    f8 = pd.Series(
        rng.choice(
            [0.0, 1.0, 2.0, 3.0, 4.0],
            size=n,
            p=[0.60, 0.18, 0.10, 0.06, 0.06],
        )
    )
    log.info("  F8 trigger_type     — SYNTHETIC injection OK")

    features = pd.DataFrame({
        "F1_url_length":              f1.values,
        "F2_num_subdomains":          f2.values,
        "F3_has_suspicious_keywords": f3.values,
        "F4_contains_ip_address":     f4.values,
        "F5_is_https":                f5.values,
        "F6_time_of_day_encoded":     f6.values,
        "F7_session_fatigue_index":   f7.values,
        "F8_trigger_type_encoded":    f8.values,
    }).reset_index(drop=True)

    target = label_col.reset_index(drop=True)

    log.info(
        "  Matrix ready: %d rows | phishing=%d (%.1f%%) | legitimate=%d (%.1f%%)",
        n, target.sum(), target.mean() * 100,
        (target == 0).sum(), (1 - target.mean()) * 100,
    )
    return features, target


def _resolve_label(df: pd.DataFrame, dataset_name: str) -> pd.Series:
    """
    Normalize any label column to: 1=phishing, 0=legitimate.

    PhiUSIIL : 'label' column — 0=phishing, 1=legitimate  -> flip
    Kaggle   : 'Result' column — 1=phishing, -1=legitimate -> remap
    """
    if "label" in df.columns:
        return (df["label"] == 0).astype(int)

    if "Result" in df.columns:
        # 1=phishing, -1=legitimate, 0=suspicious (treat as phishing)
        return df["Result"].map({1: 1, -1: 0, 0: 1}).fillna(0).astype(int)

    # Last resort: search for any label-like column
    for candidate in ["class", "target", "phishing"]:
        match = next((c for c in df.columns if candidate in c.lower()), None)
        if match:
            log.warning("Using '%s' as label column for %s.", match, dataset_name)
            s = df[match]
            if set(s.unique()).issubset({-1, 0, 1}):
                return s.map({1: 1, -1: 0, 0: 1}).fillna(0).astype(int)
            return s.astype(int)

    log.error("Cannot find a label column in %s. Columns: %s", dataset_name, list(df.columns))
    sys.exit(1)


# ===========================================================================
# STEP 3 — Train on PhiUSIIL
# ===========================================================================

def train_model(X: pd.DataFrame, y: pd.Series):
    from xgboost import XGBClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

    log.info("Splitting PhiUSIIL 80/20 for training...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    log.info("  Train: %d rows | Internal test: %d rows", len(X_train), len(X_test))

    log.info("Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

    y_pred   = model.predict(X_test)
    y_prob   = model.predict_proba(X_test)[:, 1]
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc  = roc_auc_score(y_test, y_prob)

    log.info("=" * 55)
    log.info("INTERNAL TEST RESULTS  (PhiUSIIL 20%% held-out)")
    log.info("=" * 55)
    log.info("  Accuracy : %.2f%%  (DDD target: 85%%+)", accuracy * 100)
    log.info("  ROC-AUC  : %.4f", roc_auc)
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "Phishing"]))

    if accuracy >= 0.85:
        log.info("Accuracy target MET on internal test set.")
    else:
        log.warning("Accuracy %.2f%% below 85%% — review feature engineering.", accuracy * 100)

    log.info("Feature importance (F1-F8):")
    importance = dict(zip(X.columns, model.feature_importances_))
    for feat, score in sorted(importance.items(), key=lambda x: -x[1]):
        log.info("  %-35s %.4f  %s", feat, score, "█" * int(score * 40))

    return model


# ===========================================================================
# STEP 4 — Cross-validate on Kaggle 10k
# ===========================================================================

def cross_validate_kaggle(model, X_kaggle: pd.DataFrame, y_kaggle: pd.Series) -> None:
    from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

    log.info("=" * 55)
    log.info("CROSS-VALIDATION  (Kaggle 10k — completely unseen source)")
    log.info("=" * 55)

    classes_present = y_kaggle.unique()
    if len(classes_present) < 2:
        log.warning(
            "Kaggle dataset contains only one class (%s). "
            "ROC-AUC and full classification report are not available. "
            "Reporting per-class precision/recall only.",
            "Phishing" if classes_present[0] == 1 else "Legitimate",
        )
        y_pred   = model.predict(X_kaggle)
        accuracy = accuracy_score(y_kaggle, y_pred)
        log.info("  Accuracy : %.2f%%  (DDD target: 85%%+)", accuracy * 100)
        # Use labels= to prevent sklearn mismatch on single-class data
        present_label = int(classes_present[0])
        label_name    = "Phishing" if present_label == 1 else "Legitimate"
        print(classification_report(
            y_kaggle, y_pred,
            labels=[present_label],
            target_names=[label_name],
        ))
        if accuracy >= 0.85:
            log.info("Cross-validation PASSED on single-class set.")
        else:
            log.warning("Cross-validation accuracy %.2f%% below 85%%.", accuracy * 100)
        return

    y_pred   = model.predict(X_kaggle)
    y_prob   = model.predict_proba(X_kaggle)[:, 1]
    accuracy = accuracy_score(y_kaggle, y_pred)
    roc_auc  = roc_auc_score(y_kaggle, y_prob)

    log.info("  Accuracy : %.2f%%  (DDD target: 85%%+)", accuracy * 100)
    log.info("  ROC-AUC  : %.4f", roc_auc)
    print(classification_report(y_kaggle, y_pred, target_names=["Legitimate", "Phishing"]))

    if accuracy >= 0.85:
        log.info("Cross-validation PASSED — model generalizes beyond PhiUSIIL.")
    else:
        log.warning(
            "Cross-validation accuracy %.2f%% below 85%%. "
            "Model may be overfit to PhiUSIIL. Consider mixing datasets in next sprint.",
            accuracy * 100,
        )


# ===========================================================================
# STEP 5 — Save artifact
# ===========================================================================

def save_model(model) -> None:
    model.save_model(MODEL_PATH)
    size_kb = os.path.getsize(MODEL_PATH) / 1024
    log.info("=" * 55)
    log.info("Model saved  : %s", MODEL_PATH)
    log.info("Size         : %.1f KB", size_kb)
    log.info("=" * 55)
    log.info("RiskScoringEngine will load this artifact automatically on next startup.")


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    log.info("AdaptiveSec — XGBoost Training Pipeline")
    log.info("=" * 55)

    rng = np.random.default_rng(seed=42)   # fixed seed = reproducible runs

    df_phiusiil = load_phiusiil()
    df_kaggle   = load_kaggle()

    X_phiusiil, y_phiusiil = build_feature_matrix(df_phiusiil, "PhiUSIIL", rng)
    X_kaggle,   y_kaggle   = build_feature_matrix(df_kaggle,   "Kaggle",   rng)

    model = train_model(X_phiusiil, y_phiusiil)
    cross_validate_kaggle(model, X_kaggle, y_kaggle)
    save_model(model)