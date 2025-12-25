import pandas as pd
from typing import List
from .base import BaseCheck, Warning

class DuplicateCheck(BaseCheck):
    def run(self, df: pd.DataFrame) -> List[Warning]:
        warnings = []
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            warnings.append(Warning(
                code="D001",
                name="Duplicate Rows",
                severity="warn",
                message=f"{duplicate_count} duplicate rows detected",
                fix="Use df.drop_duplicates() to remove redundant rows"
            ))
        return warnings
