import pandas as pd
import os
from datetime import datetime


DATA_DIR = "data"


def check_data_exists():
    required_files = [
        'fields.csv',
        'top_subfields_us.csv',
        'subfield_funders_us.csv',
        'top_topics_us.csv',
        'subfield_topics_us.csv',
        # NEW FILES
        'yearly_subfields.csv',
        'yearly_subfield_topics.csv'
    ]
    
    missing_files = []
    for file in required_files:
        filepath = os.path.join(DATA_DIR, file)
        if not os.path.exists(filepath):
            missing_files.append(file)
    
    if missing_files:
        print("ERROR: Missing required data files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True


def load_all_data():
    data = {}
    
    # Standard Data
    data['fields'] = pd.read_csv(os.path.join(DATA_DIR, 'fields.csv'))
    data['subfields'] = pd.read_csv(os.path.join(DATA_DIR, 'top_subfields_us.csv'))
    data['funders'] = pd.read_csv(os.path.join(DATA_DIR, 'subfield_funders_us.csv'))
    data['topics'] = pd.read_csv(os.path.join(DATA_DIR, 'top_topics_us.csv'))
    data['subfield_topics'] = pd.read_csv(os.path.join(DATA_DIR, 'subfield_topics_us.csv'))
    
    # New Yearly Data
    yearly_sf_path = os.path.join(DATA_DIR, 'yearly_subfields.csv')
    if os.path.exists(yearly_sf_path):
        data['yearly_subfields'] = pd.read_csv(yearly_sf_path)
        
    yearly_tp_path = os.path.join(DATA_DIR, 'yearly_subfield_topics.csv')
    if os.path.exists(yearly_tp_path):
        data['yearly_topics'] = pd.read_csv(yearly_tp_path)
    
    return data


def display_summary(data):
    
    fetch_date = data['fields']['fetch_date'].iloc[0] if 'fetch_date' in data['fields'].columns else 'Unknown'
    
    print("=" * 80)
    print(f"PHYSICAL SCIENCES ANALYSIS - US FOCUS")
    print(f"Data last updated: {fetch_date}")
    print("=" * 80)
    print()
    
    print("ALL FIELDS IN DOMAIN (Global):")
    print("-" * 80)
    for idx, row in data['fields'].iterrows():
        print(f"{idx+1:2d}. {row['name']:40s} (ID: {str(row['id']):10s}) Topics: {row['topics_count']:,}")
    
    print()
    print("=" * 80)
    
    print("TOP 10 SUBFIELDS (All-Time Accumulation):")
    print("-" * 80)
    for idx, row in data['subfields'].iterrows():
        print(f"{idx+1:2d}. {row['name']:50s} (ID: {str(row['id']):10s}) US Works: {row['us_works_count']:,}")
    
    print()
    print("=" * 80)
    
    # --- NEW SUMMARY SECTION FOR YEARLY DATA ---
    if 'yearly_subfields' in data:
        print("YEARLY TRENDS DATA:")
        print("-" * 80)
        df = data['yearly_subfields']
        years = sorted(df['year'].unique())
        print(f"Years Available: {min(years)} to {max(years)}")
        print(f"Total Data Points: {len(df)} subfield records")
        
        # Show sample of latest year
        latest_year = max(years)
        print(f"\nTop Subfields in {latest_year}:")
        latest_df = df[df['year'] == latest_year].head(5)
        for idx, row in latest_df.iterrows():
             print(f"  - {row['name']} ({row['us_works_count']:,} works)")
    else:
        print("YEARLY TRENDS DATA: MISSING")

    print()
    print("=" * 80)


def main():
    if not check_data_exists():
        return
    
    print("Loading data from CSV files...")
    data = load_all_data()
    print(f"✓ Data loaded successfully!\n")
    
    display_summary(data)
    
if __name__ == "__main__":
    main()
