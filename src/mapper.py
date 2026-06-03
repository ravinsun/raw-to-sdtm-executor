import pandas as pd
from src.loader import load_mapping_spec, load_raw_data
from src.derivations import format_date, concat_ids

def map_domain(domain):
    mapping, ct_dict = load_mapping_spec()
    raw_df = load_raw_data(domain)
    domain_map = mapping[mapping["sdtm_domain"] == domain.upper()]
    output_rows = []
    for _, raw_row in raw_df.iterrows():
        sdtm_row = {}
        for _, spec in domain_map.iterrows():
            raw_var  = spec["raw_variable"]
            sdtm_var = spec["sdtm_variable"]
            rule     = spec["derivation_rule"]
            if rule == "direct_map":
                sdtm_row[sdtm_var] = raw_row.get(raw_var, None)
            elif rule == "format_date":
                raw_val = raw_row.get(raw_var, None)
                sdtm_row[sdtm_var] = format_date(raw_val) if pd.notna(raw_val) else None
            elif rule == "concat_ids":
                sdtm_row[sdtm_var] = concat_ids(raw_row)
        output_rows.append(sdtm_row)
    return pd.DataFrame(output_rows)

def map_all_domains():
    results = {}
    for domain in ["dm", "lb", "ae", "vs"]:
        results[domain.upper()] = map_domain(domain)
        print(f"Mapped {domain.upper()}: {len(results[domain.upper()])} rows, {len(results[domain.upper()].columns)} variables")
    return results

if __name__ == "__main__":
    results = map_all_domains()
    for domain, df in results.items():
        print(f"--- {domain} sample ---")
        print(df.head(2).to_string())
