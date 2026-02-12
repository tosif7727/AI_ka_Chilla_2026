"""
Rainfall Data Downloader (Safe Dynamic)
Dataset  : GPM IMERG Monthly (NASA Earthdata)
Provider : GES DISC
Region   : Pakistan
"""

import earthaccess
import os
from datetime import date, timedelta

# ------------------------------
# CONFIGURATION
# ------------------------------
START_DATE = date(2015, 1, 1)  # start of data
TODAY = date.today()           # dynamic end date (today)

# Pakistan bounding box (lon_min, lat_min, lon_max, lat_max)
BBOX = (60, 20, 78, 38)
OUTPUT_DIR = "data/rainfall"

# ------------------------------
# CREATE OUTPUT DIRECTORY
# ------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------
# LOGIN TO EARTHDATA
# ------------------------------
earthaccess.login(strategy="netrc")

# ------------------------------
# SAFE FUNCTION TO GENERATE MONTHLY RANGES
# ------------------------------
def generate_monthly_ranges(start, end):
    """Generate (start, end) tuples for each month"""
    ranges = []
    current = start
    while current <= end:
        # Calculate last day of current month
        if current.month == 12:
            month_end = date(current.year, 12, 31)
        else:
            month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
        # Clip to overall end
        if month_end > end:
            month_end = end
        ranges.append((current.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")))
        # Move to first day of next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return ranges

# ------------------------------
# GENERATE SAFE DATE RANGES
# ------------------------------
date_ranges = generate_monthly_ranges(START_DATE, TODAY)

# ------------------------------
# SEARCH AND DOWNLOAD
# ------------------------------
for start, end in date_ranges:
    print(f"🔍 Searching rainfall data from {start} to {end}...")
    try:
        results = earthaccess.search_data(
            short_name="GPM_3IMERGM",
            temporal=(start, end),
            bounding_box=BBOX,
            provider="GES_DISC"
        )
        print(f"Found {len(results)} files for {start} → {end}")
        if results:
            earthaccess.download(
                results,
                local_path=OUTPUT_DIR,
                provider="GES_DISC",
                threads=1  # safest option
            )
    except Exception as e:
        print(f"⚠️ Skipped {start} → {end}: {e}")

print("✅ Rainfall data download complete")
