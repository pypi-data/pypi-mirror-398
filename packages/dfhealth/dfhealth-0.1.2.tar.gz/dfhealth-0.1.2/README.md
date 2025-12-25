# dfhealth 🏥

**Stop shipping dirty data.** `dfhealth` is an opinionated, zero-config tool to sanity-check your pandas DataFrames before they hit your models. 

Think of it like **PyLint for DataFrames**.

## Why dfhealth?
Data scientists often spend 80% of their time cleaning data. `dfhealth` automates the "sanity check" phase by flagging silent killers in your dataset with actionable advice.

## Key Checks
| Code | Name | What it catches |
| :--- | :--- | :--- |
| **D001** | Duplicate Rows | Identical rows that might skew your statistics. |
| **I001** | ID Integrity | Duplicate values in columns that look like IDs (e.g., `user_id`). |
| **N001** | Negative Values | Negative numbers in fields meant to be positive (e.g., `age`, `price`). |
| **O001** | Extreme Outliers | Values outside the 3x IQR range that could be data entry errors. |
| **T001** | Date-like String | Object columns that look like they should be datetime objects. |

## 📦 Installation
```bash
pip install dfhealth
```

## Quick Start
```python
import pandas as pd
import dfhealth as dh

# Load your dataset
df = pd.read_csv("data.csv")

# Run the health check
report = dh.health_check(df)

# Get a beautiful, colored report in your terminal
report.print()
```

## 📖 License
MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing
Want to add a new check? Check out [CONTRIBUTING.md](CONTRIBUTING.md).
