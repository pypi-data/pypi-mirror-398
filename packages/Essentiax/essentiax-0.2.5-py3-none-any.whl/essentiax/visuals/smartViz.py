"""
smartViz.py — EssentiaX Manual Smart Visualization
=================================================
NO AUTO SELECTION — USER CHOOSES THE VARIABLES
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)


# ===================================================================
# MAIN FUNCTION — MANUAL COLUMN SELECTION ONLY
# ===================================================================
def smart_viz(
    df: pd.DataFrame,
    specific_columns: list,
    target_column: str = None,
    sample_size: int = 10000,
    max_categories_plot: int = 20,
    show_plots: bool = True,
    plot_types: list = None
):
    """
    Manual visualization (NO AUTO-SELECT)

    Parameters:
    -----------
    df : DataFrame
    specific_columns : list
        Columns you WANT to visualize (MANDATORY)
    target_column : str (optional)
        Target variable for grouping
    sample_size : int
    max_categories_plot : int
    show_plots : bool
    plot_types : list
        ['distribution', 'boxplot', 'categorical', 'scatter']
    """

    print("\n📊 **EssentiaX Visualization (Manual Mode)**")
    print("=" * 60)

    # Validate columns
    missing = [c for c in specific_columns if c not in df.columns]
    if missing:
        raise ValueError(f"❌ Columns not found: {missing}")

    # Sampling
    if len(df) > sample_size:
        df_sample = df.sample(sample_size, random_state=42)
        print(f"⚡ Using {sample_size:,} rows (original {len(df):,})")
    else:
        df_sample = df.copy()
        print(f"📊 Using all {len(df):,} rows")

    # Column types
    numeric_cols = df_sample[specific_columns].select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_sample[specific_columns].select_dtypes(include=['object', 'category']).columns.tolist()

    print("\n📋 Visualization Plan:")
    print(f"   Numeric:       {len(numeric_cols)}")
    print(f"   Categorical:   {len(categorical_cols)}")
    if target_column:
        print(f"   Target:        {target_column}")

    if plot_types is None:
        plot_types = ['distribution', 'boxplot', 'categorical', 'scatter']

    plot_count = 0

    # ==========================================================
    # NUMERIC DISTRIBUTION
    # ==========================================================
    if 'distribution' in plot_types and numeric_cols:
        print("\n[1] 📈 Distribution Plots")

        for col in numeric_cols:
            plt.figure(figsize=(10, 5))
            sns.histplot(df_sample[col], kde=True)
            plt.title(f"Distribution: {col}", fontsize=14)
            plt.tight_layout()
            if show_plots: plt.show()
            plot_count += 1

    # ==========================================================
    # NUMERIC BOX PLOTS
    # ==========================================================
    if 'boxplot' in plot_types and numeric_cols:
        print("\n[2] 📦 Box Plots")

        for col in numeric_cols:
            plt.figure(figsize=(10, 5))

            if target_column and df_sample[target_column].nunique() <= 20:
                sns.boxplot(data=df_sample, x=target_column, y=col, palette='Set2')
                plt.title(f"{col} by {target_column}")
            else:
                sns.boxplot(x=df_sample[col], color='lightgreen')
                plt.title(f"Boxplot: {col}")

            plt.tight_layout()
            if show_plots: plt.show()
            plot_count += 1

    # ==========================================================
    # CATEGORICAL PLOTS (FIXED & SAFE)
    # ==========================================================
    if 'categorical' in plot_types and categorical_cols:
        print("\n[3] 🏷️ Categorical Plots")

        for col in categorical_cols:
            uniq = df_sample[col].nunique()
            if uniq > max_categories_plot:
                print(f"⏭️ Skipping '{col}' ({uniq} categories)")
                continue

            plt.figure(figsize=(12, 6))

            if target_column and df_sample[target_column].nunique() <= 20:
                sns.countplot(data=df_sample, y=col, hue=target_column, palette="viridis")
                plt.title(f"{col} by {target_column}")
            else:
                sns.countplot(data=df_sample, y=col, palette="viridis")
                plt.title(col)

            plt.tight_layout()
            if show_plots: plt.show()
            plot_count += 1

    # ==========================================================
    # SCATTER (NUMERIC VS TARGET)
    # ==========================================================
    if 'scatter' in plot_types and target_column and target_column in df.columns:
        if df[target_column].dtype in [np.int64, np.float64] and numeric_cols:
            print("\n[4] 📍 Scatter Plots")

            for col in numeric_cols[:5]:
                plt.figure(figsize=(10, 6))
                plt.scatter(df_sample[col], df_sample[target_column], alpha=0.5)
                plt.xlabel(col)
                plt.ylabel(target_column)
                plt.title(f"{col} vs {target_column}")
                plt.grid(alpha=0.3)
                if show_plots: plt.show()
                plot_count += 1

    # ==========================================================
    # SUMMARY
    # ==========================================================
    print("=" * 60)
    print(f"✅ Completed — Total Plots: {plot_count}")
    print("=" * 60)
