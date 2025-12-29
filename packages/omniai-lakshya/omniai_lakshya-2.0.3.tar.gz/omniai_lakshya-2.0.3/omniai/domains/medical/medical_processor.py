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

class MedicalProcessor:
    """Specialized medical data processor"""
    
    def __init__(self):
        self.medical_rules = self._load_medical_rules()
    
    def _load_medical_rules(self):
        """Load medical domain knowledge"""
        return {
            "sensitive_columns": ['patient_id', 'name', 'ssn', 'dob', 'mrn'],
            "critical_columns": ['diagnosis', 'treatment', 'medications'],
            "normal_ranges": {
                'age': (0, 120),
                'bp_systolic': (70, 200),
                'bp_diastolic': (40, 120),
                'heart_rate': (40, 180),
                'temperature': (35, 42),
                'spo2': (70, 100)
            }
        }
    
    def process(self, df):
        """Apply medical-specific processing"""
        print("   • Applying medical intelligence...")
        
        # 1. Flag sensitive data
        self._flag_sensitive_data(df)
        
        # 2. Validate medical ranges
        self._validate_medical_ranges(df)
        
        # 3. Create medical features
        df = self._create_medical_features(df)
        
        # 4. Add medical metadata
        df = self._add_medical_metadata(df)
        
        print("   • Medical processing complete")
        return df
    
    def _flag_sensitive_data(self, df):
        """Flag PHI (Protected Health Information)"""
        for col in df.columns:
            col_lower = str(col).lower()
            for sensitive in self.medical_rules["sensitive_columns"]:
                if sensitive in col_lower:
                    print(f"   • ⚠️ Sensitive column detected: {col}")
    
    def _validate_medical_ranges(self, df):
        """Validate medical values against normal ranges"""
        for col, (min_val, max_val) in self.medical_rules["normal_ranges"].items():
            if col in df.columns:
                outliers = df[(df[col] < min_val) | (df[col] > max_val)]
                if len(outliers) > 0:
                    print(f"   • ⚠️ {len(outliers)} outliers in {col} "
                          f"(expected {min_val}-{max_val})")
    
    def _create_medical_features(self, df):
        """Create useful medical features"""
        # Example: Create age groups
        if 'age' in df.columns:
            df['age_group'] = pd.cut(df['age'], 
                                     bins=[0, 12, 18, 30, 50, 65, 120],
                                     labels=['Child', 'Teen', 'Young', 'Adult', 
                                             'Middle', 'Senior'])
        
        # Example: Create BMI if height/weight available
        if all(col in df.columns for col in ['height_cm', 'weight_kg']):
            df['bmi'] = df['weight_kg'] / ((df['height_cm']/100) ** 2)
        
        return df
    
    def _add_medical_metadata(self, df):
        """Add medical metadata to dataframe"""
        df.attrs['medical_processed'] = True
        df.attrs['medical_rules_applied'] = list(self.medical_rules.keys())
        return df