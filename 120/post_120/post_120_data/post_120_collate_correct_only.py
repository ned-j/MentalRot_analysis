import pandas as pd
import os
import glob
import os
from pathlib import Path

'''
Scans any folder for .csv files
Detects RT + correctness columns
Keeps correct trials only
Extracts angle + RT, coercing to numeric
Adds participant ID (from file or column)
Produces long, wide, and summary outputs
'''


# ========= SETTINGS =========
data_dir = "/Users/ned/GitHub/MentalRot_analysis/120/post_120/post_120_data"   # folder containing CSVs, "." means current directory
os.makedirs("post_outputs", exist_ok=True)
output_prefix = "/Users/ned/GitHub/MentalRot_analysis/120/post_120/post_outputs/MentalRotation_CORRECT_ONLY"
angle_col = "angle"

# RT/correctness column pairs to search for (priority order)
rt_corr_pairs = [
    ("trials.key_resp.rt", "trials.key_resp.corr"),
    ("key_resp.rt", "key_resp.corr"),
    ("key_rest.rt", "key_rest.corr")
]

# ============================

csv_files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
long_rows = []
problems = []

for f in csv_files:
    try:
        df = pd.read_csv(f)

        # --- Identify RT + corr columns ---
        rt_col = corr_col = None

        # try matching RT + corr pairs
        for rt, corr in rt_corr_pairs:
            if rt in df.columns and corr in df.columns:
                rt_col, corr_col = rt, corr
                break

        # fallback: RT exists, but matching corr is different
        if rt_col is None:
            for rt, corr in rt_corr_pairs:
                if rt in df.columns:
                    rt_col = rt
                    # find ANY correctness column
                    for c in ["trials.key_resp.corr", "key_resp.corr", "key_rest.corr"]:
                        if c in df.columns:
                            corr_col = c
                            break
                    break

        if rt_col is None:
            problems.append(f"No RT column found in {f}")
            continue

        # --- Angle column (case‑insensitive) ---
        if angle_col in df.columns:
            angle_key = angle_col
        else:
            lower_map = {c.lower(): c for c in df.columns}
            if angle_col.lower() in lower_map:
                angle_key = lower_map[angle_col.lower()]
            else:
                problems.append(f"No angle column in {f}")
                continue

        # --- Extract the needed data ---
        needed_cols = [angle_key, rt_col]
        if corr_col and corr_col in df.columns:
            needed_cols.append(corr_col)

        sub = df[needed_cols].copy()

        # --- Filter correct trials only ---
        if corr_col in sub.columns:
            sub = sub[sub[corr_col] == 1]

        # --- Rename to standardised names ---
        sub = sub.rename(columns={
            angle_key: "Angle",
            rt_col: "ReactionTime_s"
        })

        # numeric coercion
        sub["Angle"] = pd.to_numeric(sub["Angle"], errors="coerce")
        sub["ReactionTime_s"] = pd.to_numeric(sub["ReactionTime_s"], errors="coerce")
        sub = sub.dropna(subset=["Angle", "ReactionTime_s"])

        # sort by angle
        sub = sub.sort_values("Angle")

        # --- Determine participant ID ---
        id_val = None
        for pcol in ["participant", "Participant", "PARTICIPANT"]:
            if pcol in df.columns:
                non_null = df[pcol].dropna()
                if len(non_null):
                    id_val = str(non_null.iloc[0])
                    break

        if id_val is None:
            id_val = Path(f).stem

        sub["ID"] = id_val
        sub["SourceFile"] = os.path.basename(f)
        sub["ReactionTime_ms"] = sub["ReactionTime_s"] * 1000

        long_rows.append(sub)

    except Exception as e:
        problems.append(f"Error in {f}: {e}")

# --- Combine all files ---
if not long_rows:
    raise RuntimeError("No valid CSVs found. Problems:\n" + "\n".join(problems))

long_df = pd.concat(long_rows, ignore_index=True)

# --- Save LONG table ---
long_csv = f"{output_prefix}_LONG.csv"
long_df.to_csv(long_csv, index=False)

# --- WIDE format (Angle × Participant mean RT) ---
wide_df = (long_df.groupby(["Angle", "ID"], as_index=False)["ReactionTime_s"]
           .mean()
           .pivot(index="Angle", columns="ID", values="ReactionTime_s")
           .sort_index())
wide_csv = f"{output_prefix}_WIDE.csv"
wide_df.to_csv(wide_csv)

# --- Summary across all participants ---
summary_df = (long_df.groupby("Angle", as_index=False)
              .agg(N=("ReactionTime_s", "count"),
                   Mean_RT_s=("ReactionTime_s", "mean"),
                   SD_RT_s=("ReactionTime_s", "std"),
                   Median_RT_s=("ReactionTime_s", "median"),
                   Min_RT_s=("ReactionTime_s", "min"),
                   Max_RT_s=("ReactionTime_s", "max"))
              .sort_values("Angle"))
summary_csv = f"{output_prefix}_SUMMARY.csv"
summary_df.to_csv(summary_csv, index=False)

print("Done!")
print("Files created:")
print(long_csv)
print(wide_csv)
print(summary_csv)
print("Problems:", problems)