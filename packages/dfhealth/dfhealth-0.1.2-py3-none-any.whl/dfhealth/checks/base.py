from abc import ABC, abstractmethod
import pandas as pd
from typing import List

class Warning:
    def __init__(self, code: str, name: str, severity: str, message: str, column: str = None, fix: str = None):
        self.code = code
        self.name = name
        self.severity = severity
        self.message = message
        self.column = column
        self.fix = fix

    def __eq__(self, other):
        if not isinstance(other, Warning):
            return False
        return (self.code == other.code and 
                self.name == other.name and 
                self.severity == other.severity and 
                self.message == other.message and 
                self.column == other.column and 
                self.fix == other.fix)

    def __hash__(self):
        return hash((self.code, self.name, self.severity, self.message, self.column, self.fix))

    def __repr__(self):
        col_str = f" [Column: {self.column}]" if self.column else ""
        return f"[{self.severity.upper()}] {self.code} ({self.name}): {self.message}{col_str}"

class BaseCheck(ABC):
    @abstractmethod
    def run(self, df: pd.DataFrame) -> List[Warning]:
        """Run the check on the dataframe and return a list of warnings."""
        pass
