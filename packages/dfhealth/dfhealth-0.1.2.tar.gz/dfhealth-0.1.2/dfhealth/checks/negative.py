import pandas as pd
from typing import List
from .base import BaseCheck, Warning

class NegativeValueCheck(BaseCheck):
    def run(self, df: pd.DataFrame) -> List[Warning]:
        warnings = []
        # Get numerical columns
        num_cols = df.select_dtypes(include=['number']).columns.unique()
        for col in num_cols:
            # Handle potentially multiple columns with same name by selecting one column at a time
            # if df[col] is a DataFrame, .iloc[:, 0] gets the first one.
            # But better to just check if it's a series or dataframe.
            series = df[col]
            if isinstance(series, pd.DataFrame):
                # If multiple columns have same name, we check each once separately?
                # For now, let's just make sure we don't crash and don't duplicate.
                # Actually, iterate by position to be absolutely safe.
                pass
            
            # Simple fix: iterate UNIQUE columns, and if multiple exist, they should be processed once.
            neg_count = (series < 0).sum()
            if isinstance(neg_count, pd.Series):
                # Multiple columns had this name
                for sub_col_name, count in neg_count.items():
                    if count > 0:
                        warnings.append(Warning(
                            code="N001",
                            name="Negative Values",
                            severity="warn",
                            message=f"Column '{col}' contains {count} negative values",
                            column=col,
                            fix="Check if negative values are valid for this field (e.g., 'age' or 'price' should usually be positive)"
                        ))
                continue

            if neg_count > 0:
                warnings.append(Warning(
                    code="N001",
                    name="Negative Values",
                    severity="warn",
                    message=f"Column '{col}' contains {neg_count} negative values",
                    column=col,
                    fix="Check if negative values are valid for this field (e.g., 'age' or 'price' should usually be positive)"
                ))
        return warnings
