# essentiax/summary/eda_pro.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime


def _fig_to_base64(fig):
    """Convert a Matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def smart_eda_pro(
    df: pd.DataFrame,
    target: str | None = None,
    report_path: str = "essentiax_report.html",
    sample_size: int | None = 5000,
    max_cat_unique: int = 50,
) -> str:
    """
    Essentiax Pro EDA:
    Generate an HTML EDA report (tables + charts) for ANY DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataset.
    target : str, optional
        Name of target column (for ML-focused analysis).
    report_path : str
        Output HTML file path.
    sample_size : int, optional
        If dataset is large, use a sample for plots & correlations.
    max_cat_unique : int
        Max unique values to treat a column as 'categorical summary candidate'.

    Returns
    -------
    str
        Path to the generated HTML report.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("smart_eda_pro expects a pandas DataFrame.")

    sns.set(style="whitegrid")

    # Sampling for heavy stuff
    original_rows = len(df)
    if sample_size and original_rows > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42)
    else:
        df_sample = df

    n_rows, n_cols = df.shape
    dtypes = df.dtypes

    # Basic column groups
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Missing & duplicates
    missing = df.isna().sum()
    missing_pct = (missing / n_rows * 100).round(2)
    missing_df = (
        pd.DataFrame({"Missing_Count": missing, "Missing_%": missing_pct})
        .loc[missing > 0]
        .sort_values("Missing_Count", ascending=False)
    )
    dup_count = df.duplicated().sum()

    # ------------------------------------------------------------------
    # 1) BASIC HTML SKELETON
    # ------------------------------------------------------------------
    sections: list[str] = []

    # Dataset overview
    overview_html = f"""
    <section>
      <h2>1. Dataset Overview</h2>
      <ul>
        <li><b>Shape:</b> {n_rows:,} rows × {n_cols} columns</li>
        <li><b>Total cells:</b> {n_rows * n_cols:,}</li>
        <li><b>Duplicates:</b> {dup_count:,} rows ({dup_count / max(n_rows,1):.2%})</li>
        <li><b>Memory usage:</b> {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB</li>
      </ul>
      <h3>Column Types</h3>
      {dtypes.to_frame("dtype").to_html(classes="simple-table", border=0)}
    </section>
    """
    sections.append(overview_html)

    # Missing values
    if not missing_df.empty:
        missing_html = f"""
        <section>
          <h2>2. Missing Values</h2>
          <p><b>Total missing cells:</b> {int(missing.sum()):,} 
             ({missing.sum() / (n_rows * n_cols):.2%} of all cells)</p>
          {missing_df.to_html(classes="simple-table", border=0)}
        </section>
        """
    else:
        missing_html = """
        <section>
          <h2>2. Missing Values</h2>
          <p><b>No missing values detected.</b></p>
        </section>
        """
    sections.append(missing_html)

    # ------------------------------------------------------------------
    # 2) NUMERIC SUMMARY + CORRELATIONS
    # ------------------------------------------------------------------
    if numeric_cols:
        desc_num = df_sample[numeric_cols].describe().T

        num_html = f"""
        <section>
          <h2>3. Numeric Features</h2>
          <p><b>Numeric columns:</b> {len(numeric_cols)}</p>
          <h3>Descriptive Statistics (sample)</h3>
          {desc_num.to_html(classes="simple-table", border=0)}
        </section>
        """
        sections.append(num_html)

        # Outlier summary (IQR based)
        outlier_rows = []
        for col in numeric_cols:
            series = df[col].dropna()
            if series.empty:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = ((series < lower) | (series > upper)).sum()
            outlier_rows.append(
                {
                    "column": col,
                    "outliers": int(outliers),
                    "outlier_%": round(outliers / len(series) * 100, 2),
                }
            )

        if outlier_rows:
            outlier_df = (
                pd.DataFrame(outlier_rows)
                .sort_values("outlier_%", ascending=False)
                .head(10)
            )
            outlier_html = f"""
            <section>
              <h3>Potential Outliers (IQR)</h3>
              {outlier_df.to_html(index=False, classes="simple-table", border=0)}
            </section>
            """
            sections.append(outlier_html)

        # Correlation heatmap
        if len(numeric_cols) > 1:
            corr = df_sample[numeric_cols].corr()

            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(
                corr,
                ax=ax,
                cmap="coolwarm",
                center=0,
                square=False,
                cbar_kws={"shrink": 0.7},
            )
            ax.set_title("Correlation Heatmap (Numeric Features)")
            img_corr = _fig_to_base64(fig)

            # Top correlated pairs
            pairs = []
            cols = corr.columns
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = corr.iloc[i, j]
                    pairs.append(
                        {
                            "Feature 1": cols[i],
                            "Feature 2": cols[j],
                            "Correlation": round(float(val), 3),
                            "Type": "Positive" if val > 0 else "Negative",
                        }
                    )
            strong_pairs = [
                p for p in pairs if abs(p["Correlation"]) >= 0.7
            ]
            corr_pairs_html = ""
            if strong_pairs:
                corr_pairs_df = pd.DataFrame(strong_pairs).sort_values(
                    "Correlation", key=lambda x: x.abs(), ascending=False
                )
                corr_pairs_html = corr_pairs_df.to_html(
                    index=False, classes="simple-table", border=0
                )
            else:
                corr_pairs_html = "<p>No strong correlations (|r| ≥ 0.7) found.</p>"

            corr_html = f"""
            <section>
              <h3>Correlation Analysis</h3>
              <img src="data:image/png;base64,{img_corr}" alt="Correlation Heatmap"/>
              <h4>Top Strong Correlations</h4>
              {corr_pairs_html}
            </section>
            """
            sections.append(corr_html)

    # ------------------------------------------------------------------
    # 3) CATEGORICAL SUMMARY
    # ------------------------------------------------------------------
    if categorical_cols:
        cat_html_parts = [
            f"<p><b>Categorical columns:</b> {len(categorical_cols)}</p>"
        ]
        for col in categorical_cols[:10]:  # limit to first 10 for readability
            vc = df[col].value_counts(dropna=False)
            top_vc = vc.head(5)
            freq_df = pd.DataFrame(
                {
                    "value": top_vc.index.astype(str),
                    "count": top_vc.values,
                    "freq_%": (top_vc.values / len(df) * 100).round(2),
                }
            )
            cat_html_parts.append(f"<h4>{col}</h4>")
            cat_html_parts.append(
                freq_df.to_html(index=False, classes="simple-table", border=0)
            )
        if len(categorical_cols) > 10:
            cat_html_parts.append(
                f"<p>... and {len(categorical_cols) - 10} more categorical columns.</p>"
            )

        cat_html = f"""
        <section>
          <h2>4. Categorical Features</h2>
          {''.join(cat_html_parts)}
        </section>
        """
        sections.append(cat_html)

    # ------------------------------------------------------------------
    # 4) TARGET ANALYSIS (IF PROVIDED)
    # ------------------------------------------------------------------
    if target is not None and target in df.columns:
        target_series = df[target]
        target_html = [f"<h2>5. Target Analysis: {target}</h2>"]

        # Detect type: classification vs regression
        nunique = target_series.nunique(dropna=True)
        if target_series.dtype in ["object", "category"] or nunique <= 20:
            problem_type = "classification"
        else:
            problem_type = "regression"

        target_html.append(f"<p><b>Detected problem type:</b> {problem_type}</p>")

        if problem_type == "classification":
            cls_counts = target_series.value_counts(dropna=False)
            cls_df = pd.DataFrame(
                {
                    "class": cls_counts.index.astype(str),
                    "count": cls_counts.values,
                    "freq_%": (cls_counts.values / len(df) * 100).round(2),
                }
            )
            target_html.append("<h3>Class Distribution</h3>")
            target_html.append(
                cls_df.to_html(index=False, classes="simple-table", border=0)
            )

            # Imbalance warning
            if len(cls_df) > 1:
                major_share = cls_df["freq_%"].max() / 100
                if major_share >= 0.8:
                    target_html.append(
                        "<p style='color:#c0392b;'><b>Warning:</b> "
                        "Severe class imbalance detected (majority class ≥ 80%).</p>"
                    )

            # Numeric features vs target (mean per class)
            if numeric_cols:
                agg = df.groupby(target)[numeric_cols].mean().round(2)
                target_html.append("<h3>Numeric Features by Class (Mean)</h3>")
                target_html.append(
                    agg.to_html(classes="simple-table", border=0)
                )

        else:  # regression
            if numeric_cols:
                corr_with_target = (
                    df[numeric_cols + [target]]
                    .corr()[target]
                    .drop(target)
                    .sort_values(key=lambda s: s.abs(), ascending=False)
                )
                corr_df = corr_with_target.reset_index()
                corr_df.columns = ["feature", "corr_with_target"]
                corr_df["abs_corr"] = corr_df["corr_with_target"].abs()
                target_html.append("<h3>Feature ↔ Target Correlations</h3>")
                target_html.append(
                    corr_df.to_html(index=False, classes="simple-table", border=0)
                )

        sections.append("<section>" + "".join(target_html) + "</section>")

    # ------------------------------------------------------------------
    # 5) SAMPLE ROWS
    # ------------------------------------------------------------------
    sample_html = f"""
    <section>
      <h2>6. Sample Rows</h2>
      {df.head(10).to_html(classes="simple-table", border=0)}
    </section>
    """
    sections.append(sample_html)

    # ------------------------------------------------------------------
    # FINAL HTML ASSEMBLY
    # ------------------------------------------------------------------
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <title>Essentiax EDA Pro Report</title>
      <style>
        body {{
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          margin: 0;
          padding: 0 20px 30px 20px;
          background: #f7f9fb;
          color: #2c3e50;
        }}
        h1 {{
          text-align: center;
          margin-top: 20px;
        }}
        h2 {{
          border-bottom: 2px solid #3498db;
          padding-bottom: 4px;
          margin-top: 30px;
        }}
        h3 {{
          margin-top: 20px;
        }}
        section {{
          background: #ffffff;
          margin-top: 20px;
          padding: 15px 20px;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .simple-table {{
          border-collapse: collapse;
          width: 100%;
          margin-top: 10px;
          font-size: 13px;
        }}
        .simple-table th, .simple-table td {{
          border: 1px solid #ecf0f1;
          padding: 6px 8px;
          text-align: left;
        }}
        .simple-table th {{
          background-color: #f0f4f8;
        }}
        img {{
          max-width: 100%;
          height: auto;
          margin-top: 10px;
          border-radius: 4px;
          border: 1px solid #ecf0f1;
        }}
        ul {{
          margin-top: 6px;
        }}
      </style>
    </head>
    <body>
      <h1>Essentiax EDA Pro Report</h1>
      <p style="text-align:center; color:#7f8c8d;">
        Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        &mdash; Rows: {n_rows:,}, Columns: {n_cols}
      </p>
      {''.join(sections)}
    </body>
    </html>
    """

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Essentiax] ✅ EDA Pro report saved to: {report_path}")
    return report_path
