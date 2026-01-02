"""
smartEDA.py
===========================================
EssentiaX – Smart Exploratory Data Analysis (EDA)

A professional-grade EDA engine that produces:
• Structural insights
• Missing value diagnostics
• Outlier detection
• Skewness analysis
• Cardinality summary
• Numeric + Categorical profiling
• Correlation intelligence
• Actionable insights

Designed to outperform Pandas-Profiling/SweetViz in clarity.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")


def smart_eda(df: pd.DataFrame, sample_size: int = 50000):
    print("\n🧠 **Starting EssentiaX Smart EDA**")
    print("=" * 70)

    # Optional Sampling (for large datasets)
    if sample_size and len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)
        print(f"📉 Dataset sampled to {sample_size:,} rows to improve speed\n")

    # BASIC STRUCTURE
    print("1️⃣ DATASET OVERVIEW")
    print("-" * 70)
    print(f"• Rows: {df.shape[0]:,}")
    print(f"• Columns: {df.shape[1]}")
    print(f"• Total Cells: {df.size:,}")
    print(f"• Memory Usage: {df.memory_usage(deep=True).sum()/1024**2:.2f} MB")
    print(f"• Duplicate Rows: {df.duplicated().sum():,}")

    # DATA TYPES
    print("\n2️⃣ DATA TYPES & COLUMN DISTRIBUTION")
    print("-" * 70)
    dtypes = df.dtypes.value_counts()
    for dtype, count in dtypes.items():
        print(f"• {dtype}: {count} columns")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    print(f"\n• Numeric Columns: {len(numeric_cols)}")
    print(f"• Categorical Columns: {len(categorical_cols)}")
    print(f"• Date Columns: {len(datetime_cols)}")

    # MISSING VALUES
    print("\n3️⃣ MISSING VALUE ANALYSIS")
    print("-" * 70)
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    if missing.empty:
        print("✔ No missing values in dataset.")
    else:
        total_missing = missing.sum()
        print(f"⚠ Missing Values Found: {total_missing:,}")
        print("\nTop Missing Columns:")
        for col, val in missing.head(8).items():
            pct = 100 * val / len(df)
            print(f"• {col:20s} → {val:8,} missing ({pct:.2f}%)")

    # NUMERIC SUMMARY
    print("\n4️⃣ NUMERIC FEATURE PROFILE")
    print("-" * 70)
    if numeric_cols:
        desc = df[numeric_cols].describe().T
        desc["skew"] = df[numeric_cols].skew()
        desc["missing_%"] = (df[numeric_cols].isnull().sum() / len(df)) * 100

        print(desc[["mean", "std", "min", "25%", "50%", "75%", "max", "skew", "missing_%"]]
              .head(8)
              .round(3)
              .to_string())

        # Outlier discovery
        print("\n📌 Outlier Detection (IQR Method)")
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower) | (df[col] > upper)][col].count()
            if outliers > 0:
                print(f"• {col}: {outliers:,} outliers")

        # Skewness ranking
        print("\n📊 Skewness Ranking (most skewed first)")
        skew_sorted = df[numeric_cols].skew().sort_values(ascending=False)
        for col, skew in skew_sorted.head(5).items():
            print(f"• {col:20s} → skew = {skew:.2f}")
    else:
        print("⚠ No numeric columns.")

    # CATEGORICAL SUMMARY
    print("\n5️⃣ CATEGORICAL FEATURE PROFILE")
    print("-" * 70)
    if categorical_cols:
        for col in categorical_cols[:8]:
            unique = df[col].nunique()
            top = df[col].value_counts().head(3)
            print(f"\n📌 {col}")
            print(f"• Unique Values: {unique}")
            for val, cnt in top.items():
                pct = 100 * cnt / len(df)
                print(f"   - {val}  ({pct:.2f}%)")

        if len(categorical_cols) > 8:
            print(f"\n... {len(categorical_cols) - 8} more categorical columns.")
    else:
        print("⚠ No categorical columns.")

    # CORRELATION ANALYSIS
    print("\n6️⃣ CORRELATION INTELLIGENCE")
    print("-" * 70)
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        strong = []

        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                val = corr.iloc[i, j]
                if abs(val) > 0.7:
                    strong.append((corr.index[i], corr.columns[j], val))

        if strong:
            strong = sorted(strong, key=lambda x: abs(x[2]), reverse=True)
            for col1, col2, val in strong[:10]:
                relation = "Positive" if val > 0 else "Negative"
                print(f"• {col1} ↔ {col2} → {val:.3f} ({relation})")
        else:
            print("No strong correlations found.")
    else:
        print("⚠ Not enough numeric columns for correlation.")

    # FINAL INSIGHTS
    print("\n" + "=" * 70)
    print("✅ EDA Completed — EssentiaX Intelligence Report")
    print("=" * 70)

    print("\n💡 Recommended Next Steps:")
    print("1. Use smart_clean() to handle missing values & encode data.")
    print("2. Remove outliers if they distort your model.")
    print("3. Normalize numerical columns before ML.")
    print("4. Perform feature engineering on categorical values.")
    print("\n")


# For local testing
if __name__ == "__main__":
    df = pd.DataFrame({
        "A": np.random.randint(1, 100, 200),
        "B": np.random.normal(50, 10, 200),
        "C": np.random.choice(["X", "Y", "Z"], 200)
    })
    df.loc[10:20, "B"] = np.nan
    smart_eda(df)
