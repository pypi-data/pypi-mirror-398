import pandas as pd
from typing import List
from .base import BaseCheck, Warning

class DateLikeCheck(BaseCheck):
    def run(self, df: pd.DataFrame) -> List[Warning]:
        warnings = []
        # Check object (string) columns
        obj_cols = df.select_dtypes(include=['object']).columns.unique()
        
        for col in obj_cols:
            # Sample a few values to check if they look like dates
            sample = df[col].dropna().head(10)
            if sample.empty:
                continue
                
            try:
                # Try to parse as datetime
                pd.to_datetime(sample, errors='raise')
                # If it didn't error, it might be a date-like string
                warnings.append(Warning(
                    code="T001",
                    name="Date-like String",
                    severity="info",
                    message=f"Column '{col}' is stored as an object but looks like a date",
                    column=col,
                    fix="Convert to datetime using pd.to_datetime(df[col]) for better analysis"
                ))
            except (ValueError, TypeError):
                pass
                
        return warnings
