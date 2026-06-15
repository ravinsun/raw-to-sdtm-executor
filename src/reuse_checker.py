import pandas as pd

def load_prior_spec(path="data/prior_study_spec.csv"):
    return pd.read_csv(path)

def reuse_lookup(variable_name: str, label: str, prior_spec: pd.DataFrame) -> dict:
    """
    Exact match on variable name against prior study spec.
    Returns domain at confidence 1.0 if found, None if not found.
    """
    match = prior_spec[
        prior_spec["variable_name"].str.upper() == variable_name.strip().upper()
    ]
    if len(match) > 0:
        row = match.iloc[0]
        return {
            "variable_name":    variable_name,
            "label":            label,
            "predicted_domain": row["domain"],
            "confidence":       1.0,
            "review_tier":      "AUTO-ACCEPT",
            "method":           "REUSE",
            "source_study":     row["source_study"],
        }
    return {
        "variable_name":    variable_name,
        "label":            label,
        "predicted_domain": None,
        "confidence":       0.0,
        "review_tier":      None,
        "method":           "NO_MATCH",
        "source_study":     None,
    }

def run_reuse_check(df: pd.DataFrame, prior_spec: pd.DataFrame) -> pd.DataFrame:
    """
    Run reuse check on a DataFrame of variables.
    Returns results with method column.
    """
    results = []
    for _, row in df.iterrows():
        result = reuse_lookup(row["variable_name"], row["label"], prior_spec)
        results.append(result)
    return pd.DataFrame(results)

if __name__ == "__main__":
    prior_spec = load_prior_spec()
    test_vars = pd.DataFrame([
        {"variable_name": "LBTEST",        "label": "Lab Test Name"},
        {"variable_name": "AESEV",         "label": "Severity of Adverse Event"},
        {"variable_name": "BMRN_ENZY_LVL", "label": "Enzyme Level Biomarker"},
        {"variable_name": "NEWVAR_XYZ",    "label": "Custom New Variable"},
        {"variable_name": "BMRN_6MWT",     "label": "Six Minute Walk Test"},
    ])
    results = run_reuse_check(test_vars, prior_spec)
    header = f"{'VARIABLE':<20} {'METHOD':<10} {'DOMAIN':<8} {'CONF':<6} SOURCE"
    print(header)
    print("-" * 60)
    for _, r in results.iterrows():
        line = "{:<20} {:<10} {:<8} {:<6} {}".format(
            r['variable_name'], r['method'],
            str(r['predicted_domain']), str(r['confidence']),
            str(r['source_study']))
        print(line)
