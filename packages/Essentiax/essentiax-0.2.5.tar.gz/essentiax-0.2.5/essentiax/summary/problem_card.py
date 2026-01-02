"""
problem_card.py
====================================
Essentiax — Dataset Problem Card (with Model Recommender)

Generates an ML-focused diagnostic report:
✔ dataset health score
✔ missing/duplicate summary
✔ high-cardinality detection
✔ target analysis + imbalance check
✔ ML problem type inference
✔ data leakage warnings
✔ model recommendations (baseline + advanced)
"""

import pandas as pd
import numpy as np


def _infer_problem_type(df: pd.DataFrame, target: str):
    """Infer ML problem type based on target column."""
    if target is None or target not in df.columns:
        return None, "no_target"

    y = df[target]
    n_unique = y.nunique()

    # Pure numeric target
    if np.issubdtype(y.dtype, np.number):
        if n_unique <= 1:
            return None, "invalid"
        if n_unique <= 20:
            return "classification", "numeric_low_card"
        return "regression", "numeric_regression"

    # Non-numeric → could be classification or NLP
    avg_len = y.astype(str).str.len().mean()
    if n_unique <= 1:
        return None, "invalid"
    if n_unique <= 30 and avg_len < 50:
        return "classification", "categorical_labels"
    if avg_len >= 50:
        return "nlp", "long_text"
    return "classification", "categorical_high_card"


def _check_imbalance(y: pd.Series):
    """Return imbalance flag + ratio of majority class if classification."""
    if y is None:
        return False, None

    if np.issubdtype(y.dtype, np.number) and y.nunique() > 20:
        return False, None  # regression, ignore

    counts = y.value_counts(normalize=True)
    if len(counts) < 2:
        return False, None

    top = counts.iloc[0]
    return bool(top > 0.8), float(top)


def _model_recommendations(problem_type, df: pd.DataFrame, target: str, imbalance_flag: bool):
    """
    Return a dict of recommended models/approaches based on:
    - problem_type: classification / regression / nlp / None
    - dataset size / feature count
    - imbalance
    """
    if problem_type is None:
        return {
            "type": "unknown",
            "baseline": [],
            "advanced": [],
            "notes": ["No target or invalid target — cannot recommend models."]
        }

    rows, cols = df.shape
    feature_cols = [c for c in df.columns if c != target]
    n_features = len(feature_cols)

    small_data = rows < 10_000
    wide_data = n_features > 100

    rec = {
        "type": problem_type,
        "baseline": [],
        "advanced": [],
        "notes": []
    }

    if problem_type == "classification":
        # Baseline
        rec["baseline"].append("LogisticRegression (with scaling)")
        rec["baseline"].append("RandomForestClassifier")

        # Advanced
        if wide_data:
            rec["advanced"].append("LinearSVC / SGDClassifier (handles many features)")
        else:
            rec["advanced"].append("GradientBoostingClassifier / XGBoost (if available)")

        if imbalance_flag:
            rec["notes"].append("Use class_weight='balanced' or resampling (SMOTE/undersampling).")

    elif problem_type == "regression":
        rec["baseline"].append("LinearRegression (check assumptions)")
        rec["baseline"].append("RandomForestRegressor")

        if wide_data:
            rec["advanced"].append("Lasso / ElasticNet (for feature selection)")
        else:
            rec["advanced"].append("GradientBoostingRegressor / XGBoostRegressor (if available)")

        if rows < 1000:
            rec["notes"].append("Small data — prefer simpler models, strong regularization, cross-validation.")

    elif problem_type == "nlp":
        rec["baseline"].append("TF-IDF + LogisticRegression / LinearSVC")
        rec["baseline"].append("TF-IDF + NaiveBayes (for text classification)")

        rec["advanced"].append("Pretrained transformers (e.g., BERT) via HuggingFace")
        rec["notes"].append("Do proper train/val/test split by time or document source to avoid leakage.")

    else:
        rec["notes"].append("Unknown problem type — treat as EDA-only for now.")

    if rows > 200_000:
        rec["notes"].append("Large dataset — consider subsampling for prototyping, then scale with efficient models.")

    return rec


def problem_card(df: pd.DataFrame, target: str = None):
    print("\n🧠 ESSENTIAX — PROBLEM CARD (ML READY + MODEL RECOMMENDER)")
    print("=" * 70)

    ROWS, COLS = df.shape

    # =========================================================
    # 1️⃣ BASIC METADATA
    # =========================================================
    print(f"📦 Dataset Shape: {ROWS:,} rows × {COLS} columns")
    mem = df.memory_usage(deep=True).sum() / 1024**2
    print(f"🧠 Memory Usage: {mem:.2f} MB")
    dup = df.duplicated().sum()
    print(f"🔁 Duplicate Rows: {dup:,}")

    # =========================================================
    # 2️⃣ MISSING VALUES
    # =========================================================
    missing = df.isnull().sum()
    missing_pct = (missing / ROWS) * 100
    missing_df = missing_pct[missing_pct > 0].sort_values(ascending=False)

    print("\n⚠ Missing Values Summary:")
    if missing_df.empty:
        print("   ✓ No missing values detected.")
    else:
        for col, pct in missing_df.head(10).items():
            print(f"   • {col:<20} → {pct:6.2f}% missing")
        if len(missing_df) > 10:
            print(f"   • ... and {len(missing_df) - 10} more columns with missing values.")

    # =========================================================
    # 3️⃣ HIGH CARDINALITY CHECK
    # =========================================================
    print("\n🔢 High-Cardinality Categorical Columns (unique > 50% of rows):")
    high_card = []
    for col in df.select_dtypes(include=['object', 'category']):
        nunq = df[col].nunique()
        if nunq > ROWS * 0.5:
            high_card.append(col)
            print(f"   • {col} ({nunq:,} unique)")

    if not high_card:
        print("   ✓ No high-cardinality categorical issues detected.")

    # =========================================================
    # 4️⃣ NUMERIC SUMMARY
    # =========================================================
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print("\n📈 Numeric Columns:", len(num_cols))

    if num_cols:
        desc = df[num_cols].describe().T[['mean', 'std', 'min', 'max']]
        print(desc.to_string())
    else:
        print("   ⚠ Dataset has NO numeric columns.")

    # =========================================================
    # 5️⃣ TARGET ANALYSIS + PROBLEM TYPE
    # =========================================================
    y = None
    problem_type, reason = _infer_problem_type(df, target)

    if target is None:
        print("\n🎯 Target: NOT PROVIDED — cannot infer ML problem type.")
    elif target not in df.columns:
        print(f"\n🎯 Target: '{target}' ❌ (column not found)")
    else:
        y = df[target]
        print(f"\n🎯 Target Column: {target}")
        print(f"   • Dtype: {y.dtype}")
        print(f"   • Unique Values: {y.nunique()}")

        if problem_type is None:
            print("   ❌ Invalid or constant target — cannot define a problem.")
        else:
            print(f"   ✔ Inferred Problem Type: {problem_type.upper()} ({reason})")

    # Imbalance check
    imbalance_flag, majority_ratio = _check_imbalance(y) if y is not None else (False, None)
    if y is not None and problem_type == "classification":
        if imbalance_flag:
            print(f"   ⚠ Class Imbalance Detected — majority class = {majority_ratio*100:.1f}%")
        else:
            print("   ✓ No severe class imbalance detected.")

    # =========================================================
    # 6️⃣ DATA LEAKAGE CHECK
    # =========================================================
    print("\n🛑 Leakage Scan:")
    potential_leaks = []
    keywords = ['id', 'identifier', 'code', 'uuid', 'ssn', 'phone', 'email']

    for col in df.columns:
        lcol = col.lower()
        for key in keywords:
            if key in lcol:
                potential_leaks.append(col)
                break

    if potential_leaks:
        for col in potential_leaks:
            print(f"   • Potential ID/leakage column: {col}")
    else:
        print("   ✓ No obvious ID/leakage columns detected.")

    # =========================================================
    # 7️⃣ DATASET HEALTH SCORE
    # =========================================================
    score = 100

    missing_pct_total = (df.isnull().sum().sum() / (ROWS * COLS)) * 100 if ROWS * COLS > 0 else 0
    if missing_pct_total > 10:
        score -= 20
    if len(high_card) > 2:
        score -= 10
    if dup > 0:
        score -= 5
    if len(num_cols) == 0:
        score -= 20
    if mem > 200:
        score -= 5
    if problem_type is None and target is not None:
        score -= 10

    score = max(int(score), 1)
    print("\n💯 Dataset Quality Score:", score, "/ 100")

    # =========================================================
    # 8️⃣ MODEL RECOMMENDATIONS
    # =========================================================
    print("\n🤖 Model Recommendations:")
    rec = _model_recommendations(problem_type, df, target, imbalance_flag)

    print(f"   • Problem Type: {rec['type']}")
    if rec["baseline"]:
        print("   • Baseline Models:")
        for m in rec["baseline"]:
            print(f"       - {m}")
    if rec["advanced"]:
        print("   • Advanced Models:")
        for m in rec["advanced"]:
            print(f"       - {m}")
    if rec["notes"]:
        print("   • Notes:")
        for n in rec["notes"]:
            print(f"       - {n}")

    # =========================================================
    # 9️⃣ RECOMMENDATIONS SUMMARY
    # =========================================================
    print("\n📝 General Recommendations:")
    if not missing_df.empty:
        print("   • Handle missing values (use smart_clean).")
    if high_card:
        print("   • High-cardinality columns → avoid naive one-hot; use target/hashing encoding.")
    if num_cols:
        print("   • Scale numeric features before training linear models.")
    if problem_type in ["classification", "regression"]:
        print("   • Do proper train/val/test split; avoid leakage from time or IDs.")

    print("\n" + "=" * 70 + "\n")
