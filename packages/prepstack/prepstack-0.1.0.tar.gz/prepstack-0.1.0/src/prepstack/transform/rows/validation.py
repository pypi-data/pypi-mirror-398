import pandas as pd
import numpy as np

def _print(guidance, *msgs):
    if guidance == "on":
        print(*msgs)

# -------------------------
# Schema validation (simple)
# -------------------------
def validate_schema(df, schema, guidance="off"):
    """
    schema: dict {col_name: dtype_str e.g. 'int64' or 'object'}
    returns True/False and prints issues if guidance on
    """
    df = df.copy()
    errors = []
    for c, expected in schema.items():
        if c not in df.columns:
            errors.append(f"Missing column: {c}")
            continue
        actual = str(df[c].dtype)
        if actual != expected:
            errors.append(f"Type mismatch for {c}: expected {expected}, got {actual}")
    if errors:
        _print(guidance, "❌ Schema validation failed:")
        for e in errors:
            _print(guidance, "  -", e)
        return False
    _print(guidance, "✅ Schema validation passed.")
    return True

# -------------------------
# Range check
# -------------------------
def range_check(df, col, min_value=None, max_value=None, guidance="off"):
    """
    Return rows violating range and print summary.
    """
    df = df.copy()
    cond = pd.Series([False]*len(df))
    if min_value is not None:
        cond = cond | (df[col] < min_value)
    if max_value is not None:
        cond = cond | (df[col] > max_value)
    violations = df[cond]
    _print(guidance, f"⚠️ Range check on '{col}': found {len(violations)} violating rows.")
    return violations

# -------------------------
# Allowed values check (categorical)
# -------------------------
def allowed_values_check(df, col, allowed_values, guidance="off"):
    df = df.copy()
    mask = ~df[col].isin(allowed_values)
    violations = df[mask]
    _print(guidance, f"⚠️ Allowed-values check on '{col}': {len(violations)} rows outside allowed set")
    return violations

# -------------------------
# Type check
# -------------------------
def type_check(df, expected_types, guidance="off"):
    """
    expected_types: dict {col: type_or_str}
    returns dict {col: True/False}
    """
    ok = {}
    for c, t in expected_types.items():
        if c not in df.columns:
            ok[c] = False
            if guidance == "on":
                print(f"⚠️ Missing column for type check: {c}")
            continue
        try:
            series = df[c].dropna()
            if series.empty:
                ok[c] = True
            else:
                if isinstance(t, str):
                    ok[c] = str(series.dtype) == t
                else:
                    ok[c] = series.map(lambda x: isinstance(x, t)).all()
        except Exception:
            ok[c] = False
    if guidance == "on":
        print("🔎 Type check results:", ok)
    return ok

# -------------------------
# Validate dataframe wrapper (runs set of checks and returns report)
# -------------------------
def validate_dataframe(df, checks, guidance="off"):
    """
    checks: dict with keys:
      - schema: {...}
      - ranges: list of dicts {'col','min','max'}
      - allowed: list of dicts {'col','allowed_values'}
      - types: dict {...}
    Returns a report dict.
    """
    report = {"schema": None, "range": [], "allowed": [], "types": None}
    if "schema" in checks:
        report["schema"] = validate_schema(df, checks["schema"], guidance=guidance)
    for r in checks.get("ranges", []):
        v = range_check(df, r["col"], r.get("min"), r.get("max"), guidance=guidance)
        report["range"].append({"col": r["col"], "violations": len(v)})
    for a in checks.get("allowed", []):
        v = allowed_values_check(df, a["col"], a["allowed_values"], guidance=guidance)
        report["allowed"].append({"col": a["col"], "violations": len(v)})
    if "types" in checks:
        report["types"] = type_check(df, checks["types"], guidance=guidance)
    _print(guidance, "✨ Validation report ready.")
    return report
