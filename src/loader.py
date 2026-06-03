import pandas as pd

def load_mapping_spec(path="data/sdtm_mapping_spec.xlsx"):
    mapping = pd.read_excel(path, sheet_name="Mapping")
    ct = pd.read_excel(path, sheet_name="Controlled_Terms")
    ct_dict = {}
    for _, row in ct.iterrows():
        ct_dict[row["sdtm_variable"]] = [v.strip() for v in str(row["allowed_values"]).split(";")]
    return mapping, ct_dict

def load_raw_data(domain):
    path = f"data/raw_edc_{domain.lower()}.csv"
    return pd.read_csv(path, dtype=str)

if __name__ == "__main__":
    mapping, ct_dict = load_mapping_spec()
    print(f"Mapping rows loaded : {len(mapping)}")
    print(f"CT variables loaded : {list(ct_dict.keys())}")
    for domain in ["dm", "lb", "ae", "vs"]:
        df = load_raw_data(domain)
        print(f"Raw {domain.upper():3s}            : {len(df)} rows")
