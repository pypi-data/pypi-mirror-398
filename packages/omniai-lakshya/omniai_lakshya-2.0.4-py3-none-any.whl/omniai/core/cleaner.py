"""
███████╗███╗   ███╗███╗   ██╗ ██╗ █████╗ 
██╔════╝████╗ ████║████╗  ██║███║██╔══██╗
█████╗  ██╔████╔██║██╔██╗ ██║╚██║╚█████╔╝
██╔══╝  ██║╚██╔╝██║██║╚██╗██║ ██║██╔══██╗
███████╗██║ ╚═╝ ██║██║ ╚████║ ██║╚█████╔╝
╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═╝ ╚════╝ 

O M N I   A I
Christmas Edition 2025
Created by: Lakshya Gupta
Date: 25 December 2025

FREE for everyone to use forever.
But this is MY work - please don't remove my name.
"""

# Your existing code continues here...
import pandas as pd
import numpy as np

class DataCleaner:
    """Universal data cleaner with domain intelligence"""
    
    def clean(self, df, domain="generic"):
        """Clean data based on domain"""
        print(f"   • Cleaning for {domain} domain")
        
        original_rows = len(df)
        original_cols = len(df.columns)
        
        # Domain-specific cleaning
        if domain == "medical":
            df_clean = self._clean_medical(df)
        elif domain == "financial":
            df_clean = self._clean_financial(df)
        else:
            df_clean = self._clean_generic(df)
        
        # Report changes
        rows_removed = original_rows - len(df_clean)
        cols_removed = original_cols - len(df_clean.columns)
        
        if rows_removed > 0:
            print(f"   • Removed {rows_removed:,} duplicate rows")
        if cols_removed > 0:
            print(f"   • Removed {cols_removed} columns")
        
        return df_clean
    
    def clean_large(self, dask_df):
        """Clean large datasets (Dask version)"""
        # This is a placeholder - would use Dask operations
        return dask_df
    
    def _clean_generic(self, df):
        """Generic cleaning rules"""
        # Remove duplicates
        df_clean = df.drop_duplicates()
        
        # Handle missing values
        df_clean = self._handle_missing_values(df_clean)
        
        # Remove constant columns
        df_clean = df_clean.loc[:, df_clean.nunique() > 1]
        
        # Fix data types
        df_clean = self._fix_data_types(df_clean)
        
        return df_clean
    
    def _clean_medical(self, df):
        """Medical-specific cleaning"""
        print("   • Medical rules: Preserving outliers, careful imputation")
        
        # Don't drop duplicates in medical data (each record might be unique)
        df_clean = df.copy()
        
        # Medical-specific: Flag missing instead of imputing
        for col in df_clean.columns:
            if df_clean[col].isnull().any():
                df_clean[f"{col}_missing"] = df_clean[col].isnull().astype(int)
        
        # Keep all columns (medical data is precious)
        return df_clean
    
    def _handle_missing_values(self, df):
        """Intelligent missing value handling"""
        for col in df.columns:
            if df[col].isnull().any():
                null_count = df[col].isnull().sum()
                null_percent = (null_count / len(df)) * 100
                
                if null_percent > 50:  # >50% missing
                    print(f"   • Warning: {col} has {null_percent:.1f}% missing")
                    # Consider dropping column
                
                elif df[col].dtype in ['float64', 'int64']:
                    # Fill numeric with median
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    print(f"   • Filled {null_count} missing in {col}")
        
        return df
    
    def _fix_data_types(self, df):
        """Fix common data type issues"""
        for col in df.columns:
            # Convert string numbers to numeric
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                    print(f"   • Converted {col} to numeric")
                except:
                    pass
        
        return df