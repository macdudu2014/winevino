# Wine Data Management Workflow

## Overview
This document describes the workflow for managing wines with missing data (no ratings or incorrect types).

## Files

### Data Files
- `wines_with_no_rating.csv` - Wines without Vivino ratings (73 wines)
- `wines_with_other_type.csv` - Wines with incorrect "Other" type
- `carrefour_wines.csv` - Source data from Carrefour
- `ah_wines.csv` - Source data from Albert Heijn
- `manual_wines.csv` - Manually added wines
- `mobile_build/wines.json` - Final compiled wine data for the app

### Scripts

#### 1. Extract Problem Wines
**Script:** `export_problem_wines.py`
**Purpose:** Finds wines with missing ratings or incorrect types from source CSVs
**Usage:**
```bash
python export_problem_wines.py
```
**Output:** Creates/updates `wines_with_no_rating.csv` and `wines_with_other_type.csv`

#### 2. Apply Corrections
**Script:** `apply_corrections.py`
**Purpose:** Applies manual corrections from problem wine CSVs back to source CSVs
**Usage:**
```bash
python apply_corrections.py
```
**What it does:**
- Reads corrections from `CORRECTED SCORE (write here)` column in `wines_with_no_rating.csv`
- Reads corrections from `CORRECTED TYPE (write here)` column in `wines_with_other_type.csv`
- Updates the source CSV files (`carrefour_wines.csv`, `ah_wines.csv`, `manual_wines.csv`)

#### 3. Regenerate wines.json
**Script:** `generate_wines_json.py`
**Purpose:** Rebuilds the final wines.json from source CSVs
**Usage:**
```bash
python generate_wines_json.py
```

## Workflow

### For Missing Ratings

1. **Extract wines without ratings:**
   ```bash
   python export_problem_wines.py
   ```

2. **Option A - Manual correction:**
   - Open `wines_with_no_rating.csv`
   - Add ratings in the `CORRECTED SCORE (write here)` column
   - Save the file

3. **Option B - Try automatic scraping:**
   ```bash
   python vivino_api_scraper.py  # Fast API-based scraper
   # OR
   python vivino_scraper.py      # Slower browser-based scraper
   ```

4. **Apply corrections back to source:**
   ```bash
   python apply_corrections.py
   ```

5. **Regenerate wines.json:**
   ```bash
   python generate_wines_json.py
   ```

### For Incorrect Wine Types

1. **Extract wines with "Other" type:**
   ```bash
   python export_problem_wines.py
   ```

2. **Manual correction:**
   - Open `wines_with_other_type.csv`
   - Add correct type in the `CORRECTED TYPE (write here)` column
   - Options: Red, White, Rosé, Sparkling, Dessert

3. **Apply corrections:**
   ```bash
   python apply_corrections.py
   ```

4. **Regenerate wines.json:**
   ```bash
   python generate_wines_json.py
   ```

## Scrapers

### vivino_api_scraper.py
- **Type:** API-based (no browser needed)
- **Speed:** Fast (~0.7s per wine)
- **Reliability:** Good for well-known wines
- **Best for:** Quick lookups, batch processing

### vivino_scraper.py
- **Type:** Browser-based (Selenium)
- **Speed:** Slower (~5s per wine)
- **Reliability:** Better for obscure wines
- **Best for:** Wines that API scraper can't find

## Current Status

- **Total wines:** ~800
- **Wines without ratings:** 73 (mostly generic/store brands)
- **Wines with incorrect type:** Check `wines_with_other_type.csv`

## Notes

- The scrapers use fuzzy matching and analyze multiple search results
- Generic wines (e.g., "Vin Blanc sec 3 L") often won't have Vivino ratings
- Store brands may not be in Vivino's database
- It's acceptable to leave some wines as "N/A" if they're not on Vivino
