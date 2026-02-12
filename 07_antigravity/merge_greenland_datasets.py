import pandas as pd
import os
import warnings

warnings.filterwarnings("ignore")

# Define paths
directory = r'd:\ai_work\07_antigravity\01_greenland\00_dataset'
output_file = r'd:\ai_work\07_antigravity\greenland_mineral_master_dataset.xlsx'

# Load datasets
print("Loading datasets...")
gmom_tracts = pd.read_excel(os.path.join(directory, "gmom_tracts.xlsx"))
grl_ne_placenames = pd.read_excel(os.path.join(directory, "grl_ne_placenames.xlsx"))
intrusions = pd.read_excel(os.path.join(directory, "intrusions.xlsx"))
mineral_occurrences_v3_external = pd.read_excel(os.path.join(directory, "mineral_occurrences_v3_external.xlsx"))
totalcore = pd.read_excel(os.path.join(directory, "totalcore.xlsx"))

# --- Data Cleaning and Standardizing ---
print("Cleaning and standardizing...")

# 1. Clean Mineral Occurrences
occ_clean = mineral_occurrences_v3_external.copy()
occ_clean['source_type'] = 'Mineral Occurrence'
occ_clean = occ_clean.rename(columns={'regionname': 'region', 'main_occ_1': 'name', 'text_searc': 'description'})
# Drop columns that are mostly empty or redundant
cols_to_drop = ['commodit_2', 'ogc_fid', 'geolfeatur', 'label_posi'] + [col for col in occ_clean.columns if 'commodity' in col and col not in ['commodity_', 'main_commo']]
occ_clean = occ_clean.drop(columns=cols_to_drop, errors='ignore')

# 2. Clean Total Core (Drillholes)
core_clean = totalcore.copy()
core_clean['source_type'] = 'Drillhole'
core_clean = core_clean.rename(columns={'drillhole_': 'name', 'locality': 'region', 'classitem_': 'description'})
core_clean = core_clean[['source_type', 'name', 'region', 'latitude', 'longitude', 'description', 'company_na', 'start_year', 'depth_to']]

# 3. Clean Intrusions
int_clean = intrusions.copy()
int_clean['source_type'] = 'Intrusion'
int_clean = int_clean.rename(columns={'name': 'name', 'classname_': 'category', 'descriptio': 'description'})
# Intrusions usually don't have lat/long in this file, we'll see if they appear in concat
int_clean = int_clean[['source_type', 'name', 'category', 'description', 'txt_search']]

# 4. Clean Placenames
place_clean = grl_ne_placenames.copy()
place_clean['source_type'] = 'Placename'
place_clean = place_clean.rename(columns={'placename': 'name', 'descriptio': 'description'})
place_clean = place_clean[['source_type', 'name', 'latitude', 'longitude', 'description']]

# 5. Clean GMOM Tracts
tracts_clean = gmom_tracts.copy()
tracts_clean['source_type'] = 'Mineral Tract'
tracts_clean = tracts_clean.rename(columns={'tract_name': 'name', 'classname_': 'category', 'mineralisa': 'description'})
tracts_clean = tracts_clean[['source_type', 'name', 'category', 'description', 'year', 'total_scor']]

# --- Concatenation ---
print("Merging datasets...")
dfs = [occ_clean, core_clean, int_clean, place_clean, tracts_clean]

# Ensure each dataframe has unique column names (some might have duplicates like 'commodity')
for i, df in enumerate(dfs):

    if not df.columns.is_unique:
        print(f"Fixing duplicate columns in dataframe {i}")
        # Rename duplicate columns by adding a suffix
        cols = pd.Series(df.columns)
        for dupe in cols[cols.duplicated()].unique():
            cols[cols[cols == dupe].index] = [f"{dupe}_{j}" if j != 0 else dupe for j in range(len(cols[cols == dupe]))]
        df.columns = cols

master_df = pd.concat(dfs, axis=0, ignore_index=True)


# Reorder columns for readability
core_cols = ['source_type', 'name', 'latitude', 'longitude', 'region', 'category', 'description']
other_cols = [c for c in master_df.columns if c not in core_cols]
master_df = master_df[core_cols + other_cols]

# --- Export ---
print(f"Exporting to {output_file}...")
master_df.to_excel(output_file, index=False)
print("Processing complete!")
print(f"Final shape: {master_df.shape}")
