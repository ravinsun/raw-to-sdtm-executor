import pandas as pd
from src.loader import load_mapping_spec

REQUIRED_VARS = {
    "DM": ["USUBJID", "SEX", "RFSTDTC"],
    "LB": ["USUBJID", "LBTEST", "LBTESTCD", "LBSTRESN", "LBDTC"],
    "AE": ["USUBJID", "AETERM", "AESEV", "AESTDTC"],
    "VS": ["USUBJID", "VSTEST", "VSTESTCD", "VSSTRESN", "VSDTC"],
}

def validate_domain(domain, sdtm_df):
    mapping, ct_dict = load_mapping_spec()
    issues = []
    for idx, row in sdtm_df.iterrows():
        for var in REQUIRED_VARS.get(domain.upper(), []):
            val = row.get(var, None)
            if pd.isna(val) or str(val).strip() in ("", "nan", "None"):
                issues.append({"check_id": "MISSING_REQUIRED", "domain": domain.upper(),
                    "variable": var, "row": idx+1, "severity": "ERROR",
                    "message": f"Required variable {var} is missing or null"})
        for var, allowed in ct_dict.items():
            if var in row.index:
                val = str(row[var]).strip().upper() if pd.notna(row[var]) else ""
                if val and val not in [a.upper() for a in allowed]:
                    issues.append({"check_id": "INVALID_CT", "domain": domain.upper(),
                        "variable": var, "row": idx+1, "severity": "ERROR",
                        "message": f"Value '{row[var]}' not in controlled terminology {allowed}"})
        date_vars = [v for v in row.index if v.endswith("DTC")]
        for var in date_vars:
            val = str(row[var]).strip() if pd.notna(row[var]) else ""
            if val and val != "nan":
                try:
                    pd.to_datetime(val, format="%Y-%m-%d")
                except:
                    issues.append({"check_id": "DATE_FORMAT", "domain": domain.upper(),
                        "variable": var, "row": idx+1, "severity": "ERROR",
                        "message": f"Value '{val}' is not ISO 8601 format (YYYY-MM-DD)"})
        numeric_vars = mapping[(mapping["sdtm_domain"] == domain.upper()) &
            (mapping["data_type"] == "float")]["sdtm_variable"].tolist()
        for var in numeric_vars:
            if var in row.index:
                val = str(row[var]).strip() if pd.notna(row[var]) else ""
                if val and val != "nan":
                    try:
                        float(val)
                    except:
                        issues.append({"check_id": "WRONG_DTYPE", "domain": domain.upper(),
                            "variable": var, "row": idx+1, "severity": "ERROR",
                            "message": f"Expected numeric, got '{val}'"})
    return pd.DataFrame(issues) if issues else pd.DataFrame(
        columns=["check_id","domain","variable","row","severity","message"])

def validate_all(sdtm_results):
    all_issues = []
    for domain, df in sdtm_results.items():
        issues = validate_domain(domain, df)
        all_issues.append(issues)
        print(f"{'OK' if len(issues)==0 else 'ISSUES'} {domain}: {len(issues)} issue(s) found")
    return pd.concat(all_issues, ignore_index=True)

if __name__ == "__main__":
    from src.mapper import map_all_domains
    results = map_all_domains()
    report = validate_all(results)
    print(f"Total issues: {len(report)}")
    print(report.to_string())
