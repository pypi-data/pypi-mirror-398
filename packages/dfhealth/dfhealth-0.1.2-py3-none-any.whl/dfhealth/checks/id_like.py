import pandas as pd
from typing import List
from .base import BaseCheck, Warning

class IDLikeCheck(BaseCheck):
    def run(self, df: pd.DataFrame) -> List[Warning]:
        warnings = []
        for col in df.columns.unique():
            # Check if column name contains 'id' and values are unique or near-unique
            if 'id' in col.lower() or 'key' in col.lower():
                is_unique = df[col].is_unique
                if not is_unique:
                    warnings.append(Warning(
                        code="I001",
                        name="ID Integrity",
                        severity="warn",
                        message=f"Column '{col}' looks like an ID but contains non-unique values",
                        column=col,
                        fix="Check if duplicates in ID column are intentional; IDs should usually be unique"
                    ))
            
            # Also check for non-ID named columns that are unique
            elif df[col].is_unique and df[col].nunique() == len(df) and len(df) > 1:
                 # Only warn if it's not a known ID pattern but behaves like one
                 # Maybe just info level?
                 pass

        return warnings
