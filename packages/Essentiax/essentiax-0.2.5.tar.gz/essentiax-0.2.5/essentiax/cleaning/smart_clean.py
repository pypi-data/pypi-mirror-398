"""
smart_clean.py — EssentiaX Clean Pro
=================================================
Universal ML-ready Data Cleaner
• Intelligent missing value handling
• Robust outlier removal (OPTIMIZED)
• Safe scaling
• High-quality encoding
• Dataset insights + warnings
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import warnings
warnings.filterwarnings('ignore')


def smart_clean(
    df: pd.DataFrame,
    missing_strategy: str = "auto",     # auto | mean | median | mode | drop
    outlier_strategy: str = "iqr",      # iqr | none
    scale_numeric: bool = True,
    encode_categorical: bool = True,
    max_cardinality: int = 50,          # Max unique values for one-hot encoding
    inplace: bool = False,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Clean and prepare any dataset for Machine Learning.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataset
    missing_strategy : str
        Strategy for missing values: 'auto', 'mean', 'median', 'mode', 'drop'
    outlier_strategy : str
        Outlier removal method: 'iqr' (IQR method) or 'none' (skip)
    scale_numeric : bool
        Apply StandardScaler to numeric columns
    encode_categorical : bool
        Apply OneHotEncoding to categorical columns
    max_cardinality : int
        Maximum unique values for one-hot encoding (prevents explosion)
    inplace : bool
        Modify original dataframe (saves memory)
    verbose : bool
        Print detailed progress information
    
    Returns:
    --------
    pd.DataFrame : Cleaned, ML-ready dataset
    """
    
    if not inplace:
        df = df.copy()
    
    if verbose:
        print("\n🧹 **EssentiaX Clean Pro: Starting Cleaning Pipeline...**")
        print("------------------------------------------------------------")
    
    original_shape = df.shape
    
    # Column Types Detection
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    
    if verbose:
        print(f"🔍 Detected {len(numeric_cols)} numeric columns")
        print(f"🔍 Detected {len(categorical_cols)} categorical columns")
    
    # ═══════════════════════════════════════════════════════
    # 1️⃣ MISSING VALUE HANDLING (FIXED)
    # ═══════════════════════════════════════════════════════
    if verbose:
        print("\n1️⃣ Handling Missing Values...")
    
    # Count missing values BEFORE handling
    missing_info = df.isna().sum()
    total_missing = missing_info.sum()
    
    if total_missing == 0:
        if verbose:
            print("   ✅ No missing values found.")
    else:
        if verbose:
            print(f"   ⚠️  Found {total_missing:,} missing values across {(missing_info > 0).sum()} columns")
            # Show top 5 columns with missing values
            top_missing = missing_info[missing_info > 0].sort_values(ascending=False).head(5)
            for col, count in top_missing.items():
                pct = 100 * count / len(df)
                print(f"      • {col}: {count:,} missing ({pct:.2f}%)")
        
        # Handle missing values column by column
        if missing_strategy == "drop":
            df = df.dropna()
            if verbose:
                print(f"   ✅ Dropped rows with missing values (removed {total_missing:,} rows)")
        else:
            filled_cols = []
            for col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count == 0:
                    continue
                
                # Determine strategy
                if missing_strategy == "auto":
                    if col in numeric_cols:
                        strategy = "median"
                    else:
                        strategy = "mode"
                else:
                    strategy = missing_strategy
                
                # Apply filling strategy
                try:
                    if strategy == "mean" and col in numeric_cols:
                        fill_value = df[col].mean()
                        df[col] = df[col].fillna(fill_value)
                        filled_cols.append(f"{col} (mean)")
                    elif strategy == "median" and col in numeric_cols:
                        fill_value = df[col].median()
                        df[col] = df[col].fillna(fill_value)
                        filled_cols.append(f"{col} (median)")
                    else:  # mode for categorical or fallback
                        mode_values = df[col].mode()
                        if len(mode_values) > 0:
                            fill_value = mode_values.iloc[0]
                            df[col] = df[col].fillna(fill_value)
                            filled_cols.append(f"{col} (mode)")
                except Exception as e:
                    if verbose:
                        print(f"   ⚠️  Warning: Could not fill {col}: {e}")
            
            # Verify all missing values are handled
            remaining_missing = df.isna().sum().sum()
            if verbose:
                if remaining_missing == 0:
                    print(f"   ✅ Missing values handled successfully ({len(filled_cols)} columns filled)")
                else:
                    print(f"   ⚠️  Warning: {remaining_missing:,} missing values remain")
    
    # ═══════════════════════════════════════════════════════
    # 2️⃣ OUTLIER REMOVAL (OPTIMIZED - SINGLE PASS)
    # ═══════════════════════════════════════════════════════
    if outlier_strategy == "iqr" and len(numeric_cols) > 0:
        if verbose:
            print("\n2️⃣ Removing Outliers (IQR Method)...")
        
        before_rows = df.shape[0]
        
        # ✅ BUILD SINGLE BOOLEAN MASK (OPTIMIZED)
        mask = pd.Series([True] * len(df), index=df.index)
        outlier_counts = {}
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR == 0:  # Skip if no variance
                continue
            
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            
            # Update mask (no dataframe copy!)
            col_mask = (df[col] >= lower) & (df[col] <= upper)
            outliers_in_col = (~col_mask).sum()
            if outliers_in_col > 0:
                outlier_counts[col] = outliers_in_col
            mask &= col_mask
        
        # ✅ APPLY MASK ONCE (single operation)
        df = df[mask]
        
        removed = before_rows - df.shape[0]
        if verbose:
            print(f"   🧮 Removed {removed:,} rows as outliers ({100*removed/before_rows:.2f}%)")
            if outlier_counts:
                top_outliers = sorted(outlier_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"   📊 Top columns with outliers:")
                for col, count in top_outliers:
                    print(f"      • {col}: {count:,} outliers")
    else:
        if verbose:
            print("\n2️⃣ Outlier Removal Skipped.")
    
    # ═══════════════════════════════════════════════════════
    # 3️⃣ SCALING (with verification)
    # ═══════════════════════════════════════════════════════
    if scale_numeric and len(numeric_cols) > 0:
        if verbose:
            print("\n3️⃣ Scaling Numeric Features (StandardScaler)...")
        
        # Update numeric columns list (may have changed after outlier removal)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) > 0:
            scaler = StandardScaler()
            df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            
            if verbose:
                # Verify scaling worked
                mean_check = df[numeric_cols].mean().abs().mean()
                std_check = df[numeric_cols].std().mean()
                print(f"   ✅ Scaled {len(numeric_cols)} numeric features.")
                print(f"   📊 Verification: mean ≈ {mean_check:.6f}, std ≈ {std_check:.3f}")
        else:
            if verbose:
                print("   ⚠️  No numeric columns to scale.")
    else:
        if verbose:
            print("\n3️⃣ Scaling Skipped.")
    
    # ═══════════════════════════════════════════════════════
    # 4️⃣ ENCODING (with cardinality check)
    # ═══════════════════════════════════════════════════════
    if encode_categorical and len(categorical_cols) > 0:
        if verbose:
            print("\n4️⃣ Encoding Categorical Features (OneHotEncoder)...")
        
        # Update categorical columns list
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        
        if len(categorical_cols) > 0:
            # Check cardinality before encoding
            safe_cols = []
            skip_cols = []
            
            for col in categorical_cols:
                unique_count = df[col].nunique()
                if unique_count <= max_cardinality:
                    safe_cols.append(col)
                else:
                    skip_cols.append((col, unique_count))
            
            # Encode safe columns
            if safe_cols:
                ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore", dtype=np.int8)
                encoded = ohe.fit_transform(df[safe_cols])
                
                encoded_df = pd.DataFrame(
                    encoded,
                    columns=ohe.get_feature_names_out(safe_cols),
                    index=df.index
                )
                
                df = df.drop(columns=safe_cols)
                df = pd.concat([df, encoded_df], axis=1)
                
                if verbose:
                    print(f"   ✅ Encoded {len(safe_cols)} categorical columns")
                    print(f"      • Created {encoded_df.shape[1]} new features")
            
            # Warn about skipped columns
            if skip_cols and verbose:
                print(f"   ⚠️  Skipped {len(skip_cols)} high-cardinality columns:")
                for col, count in skip_cols[:3]:
                    print(f"      • {col}: {count:,} unique values (limit: {max_cardinality})")
                print(f"   💡 Consider: Label encoding or dropping these columns")
        else:
            if verbose:
                print("   ℹ️  No categorical columns to encode.")
    else:
        if verbose:
            print("\n4️⃣ Encoding Skipped.")
    
    # ═══════════════════════════════════════════════════════
    # 5️⃣ SUMMARY (ENHANCED)
    # ═══════════════════════════════════════════════════════
    if verbose:
        print("\n------------------------------------------------------------")
        print("🎯 **CLEANING SUMMARY**")
        print(f"🧾 Original shape: {original_shape}")
        print(f"🧾 Final shape:    {df.shape}")
        print(f"📉 Rows removed:   {original_shape[0] - df.shape[0]:,} ({100*(original_shape[0] - df.shape[0])/original_shape[0]:.2f}%)")
        print(f"📈 Columns added:  {df.shape[1] - original_shape[1]}")
        print(f"📦 Memory usage:   {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Final verification
        print("\n🔍 Final Data Quality:")
        final_missing = df.isna().sum().sum()
        print(f"   • Missing values:  {final_missing:,} {'✅' if final_missing == 0 else '⚠️'}")
        print(f"   • Duplicates:      {df.duplicated().sum():,}")
        print(f"   • Total features:  {df.shape[1]}")
        print(f"   • ML Ready:        {'✅ YES' if final_missing == 0 else '⚠️ NO (has missing values)'}")
        
        # Insights
        print("\n📌 Applied Operations:")
        if total_missing > 0:
            print("   ✅ Missing values handled")
        if outlier_strategy == "iqr":
            print("   ✅ Outliers removed using IQR")
        if scale_numeric:
            print("   ✅ Numeric features scaled")
        if encode_categorical:
            print("   ✅ Categorical features encoded")
        
        # Warnings
        print("\n⚠️  Potential Issues:")
        warnings_found = False
        
        if len(categorical_cols) > 15:
            print("   • High number of categorical columns (may cause feature explosion)")
            warnings_found = True
        
        if len(numeric_cols) == 0:
            print("   • No numeric columns detected (ML capabilities limited)")
            warnings_found = True
        
        if df.shape[1] > 1000:
            print("   • Large feature space (consider dimensionality reduction)")
            warnings_found = True
        
        if final_missing > 0:
            print(f"   • Still has {final_missing:,} missing values (needs attention)")
            warnings_found = True
        
        if not warnings_found:
            print("   ✅ No issues detected!")
        
        print("------------------------------------------------------------")
        print("✨ **EssentiaX Clean Pro Completed!**\n")
    
    return df


# ═══════════════════════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🧪 Testing Smart Clean with sample data...\n")
    
    # Create sample dataset with problems
    np.random.seed(42)
    data = {
        'Age': [25, 30, 120, 22, 29, np.nan, 28, 150, 26, 31] * 100,
        'Salary': [50000, 60000, 1000000, 45000, 52000, np.nan, 51000, 2000000, 47000, 55000] * 100,
        'City': ['Mumbai', 'Delhi', 'Delhi', 'Pune', np.nan, 'Mumbai', 'Bangalore', 'Chennai', 'Mumbai', 'Delhi'] * 100,
        'Department': ['HR', 'IT', 'IT', 'HR', 'Finance', 'IT', 'HR', 'IT', 'Finance', 'HR'] * 100,
        'Score': [75, 80, 95, 60, 88, 72, np.nan, 91, 85, 78] * 100
    }
    
    df = pd.DataFrame(data)
    
    print("🔹 Original Data:")
    print(f"   Shape: {df.shape}")
    print(f"   Missing values: {df.isna().sum().sum()}")
    print(f"   Memory: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    # Test cleaning
    cleaned_df = smart_clean(
        df,
        missing_strategy="auto",
        outlier_strategy="iqr",
        scale_numeric=True,
        encode_categorical=True,
        max_cardinality=50,
        inplace=False,
        verbose=True
    )
    
    print("\n🔹 Cleaned Data:")
    print(f"   Shape: {cleaned_df.shape}")
    print(f"   Missing values: {cleaned_df.isna().sum().sum()}")
    print(f"   Memory: {cleaned_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    print("\n✅ Test completed!")