import pandas as pd

STUDY_ID = "BMRN-2023"

def format_date(value):
    try:
        return pd.to_datetime(value, format="%m/%d/%Y").strftime("%Y-%m-%d")
    except:
        return value

def concat_ids(row, site_col="SITE_ID", subj_col="SUBJ_ID"):
    site = str(row.get(site_col, "")).strip()
    subj = str(row.get(subj_col, "")).strip()
    return f"{STUDY_ID}-{site}-{subj}"

if __name__ == "__main__":
    print(format_date("03/15/2023"))
    print(concat_ids({"SITE_ID": "SITE01", "SUBJ_ID": "S001"}))
