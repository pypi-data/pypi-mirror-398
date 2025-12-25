import pandas as pd
from typing import List
from .checks.base import Warning, BaseCheck

class Report:
    def __init__(self, warnings: List[Warning]):
        # Deduplicate warnings while preserving order
        seen = set()
        unique_warnings = []
        for w in warnings:
            if w not in seen:
                unique_warnings.append(w)
                seen.add(w)
        self.warnings = unique_warnings

    def _get_color_prefix(self, severity: str) -> str:
        colors = {
            "error": "\033[91m", # Red
            "warn": "\033[93m",  # Yellow
            "info": "\033[94m",  # Blue
            "reset": "\033[0m",
            "bold": "\033[1m"
        }
        return colors.get(severity.lower(), "")

    def print(self):
        reset = self._get_color_prefix("reset")
        bold = self._get_color_prefix("bold")

        if not self.warnings:
            print(f"✨ {bold}No health issues detected! Your data looks healthy.{reset}")
            return

        print(f"🏥 {bold}Data Health Report: {len(self.warnings)} issues found{reset}\n")
        
        # Summary Table
        counts = {"error": 0, "warn": 0, "info": 0}
        for w in self.warnings:
            counts[w.severity.lower()] += 1
        
        print(f"{bold}Summary:{reset}")
        for sev in ["error", "warn", "info"]:
            if counts[sev] > 0:
                color = self._get_color_prefix(sev)
                print(f"  - {color}{sev.upper()}{reset}: {counts[sev]}")
        print()

        # Group by severity for better readability
        for severity in ["error", "warn", "info"]:
            severity_warnings = [w for w in self.warnings if w.severity == severity]
            if severity_warnings:
                color = self._get_color_prefix(severity)
                print(f"{color}--- {severity.upper()}S ---{reset}")
                for w in severity_warnings:
                    print(f"• {bold}{w.code} ({w.name}){reset}: {w.message}")
                    if w.column:
                        print(f"  └─ Column: {bold}{w.column}{reset}")
                    if w.fix:
                        print(f"  └─ {color}Suggested Fix:{reset} {w.fix}")
                print()

        # Add a code reference legend
        distinct_codes = {w.code: w.name for w in self.warnings}
        if distinct_codes:
            print(f"📖 {bold}Code Reference:{reset}")
            for code, name in sorted(distinct_codes.items()):
                print(f"  {code}: {name}")

def health_check(df: pd.DataFrame) -> Report:
    """Run all opinionated health checks on the DataFrame."""
    warnings = []
    
    # We will dynamically or statically import checks here
    from .checks.duplicates import DuplicateCheck
    from .checks.id_like import IDLikeCheck
    from .checks.negative import NegativeValueCheck
    from .checks.outlier import OutlierCheck
    from .checks.date_like import DateLikeCheck

    checks: List[BaseCheck] = [
        DuplicateCheck(),
        IDLikeCheck(),
        NegativeValueCheck(),
        OutlierCheck(),
        DateLikeCheck()
    ]

    for check in checks:
        warnings.extend(check.run(df))

    return Report(warnings)
