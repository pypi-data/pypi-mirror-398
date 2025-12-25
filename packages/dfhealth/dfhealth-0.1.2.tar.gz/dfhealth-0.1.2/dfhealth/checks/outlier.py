import pandas as pd
import numpy as np
from typing import List
from .base import BaseCheck, Warning

class OutlierCheck(BaseCheck):
    def run(self, df: pd.DataFrame) -> List[Warning]:
        warnings = []
        num_cols = df.select_dtypes(include=['number']).columns.unique()
        
        for col in num_cols:
            if df[col].nunique() < 5: # Skip if very few unique values
                continue
                
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 3 * iqr # Using 3*IQR for 'extreme' outliers
            upper_bound = q3 + 3 * iqr
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            outlier_count = len(outliers)
            
            if outlier_count > 0:
                warnings.append(Warning(
                    code="O001",
                    name="Extreme Outliers",
                    severity="info",
                    message=f"Column '{col}' has {outlier_count} extreme outliers",
                    column=col,
                    fix="Consider investigating values outside of [3*IQR] range"
                ))
        return warnings
