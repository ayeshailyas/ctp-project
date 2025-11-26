import os
import pandas as pd
import json

# Configuration
DATA_DIR = "data"
OUTPUT_FILE = "src/data/generated-data.json"

def get_country_stats(country_code):
    country_path = os.path.join(DATA_DIR, country_code)
    
    subfields_file = os.path.join(country_path, "top_subfields_all_time.csv")
    yearly_subfields_file = os.path.join(country_path, "yearly_subfields.csv")
    
    stats = {
        "countryCode": country_code,
        "countryName": country_code,
        "topSubfields": [],
        "trends": {}
    }

    # 1. Process Top Subfields
    top_names = []
    if os.path.exists(subfields_file):
        try:
            df = pd.read_csv(subfields_file)
            # CHANGED: Take top 10 instead of 5
            top_10 = df.head(10).rename(columns={'name': 'name', 'works_count': 'totalWorks'})
            stats["topSubfields"] = top_10[['name', 'totalWorks']].to_dict('records')
            top_names = top_10['name'].tolist()
        except Exception as e:
            print(f"  Warning: subfields error {country_code}: {e}")

    # 2. Process Yearly Trends
    if os.path.exists(yearly_subfields_file) and top_names:
        try:
            df = pd.read_csv(yearly_subfields_file)
            for subfield_name in top_names:
                sf_data = df[df['name'] == subfield_name].sort_values('year')
                trend_list = sf_data[['year', 'works_count']].rename(columns={
                    'works_count': 'volume'
                }).to_dict('records')
                stats["trends"][subfield_name] = trend_list
        except Exception as e:
            print(f"  Warning: trends error {country_code}: {e}")

    if not stats["topSubfields"]:
        return None
        
    return stats

def main():
    print("Generating top 10 interactive data...")
    all_data = {}
    if os.path.exists(DATA_DIR):
        for item in os.listdir(DATA_DIR):
            if os.path.isdir(os.path.join(DATA_DIR, item)):
                country_data = get_country_stats(item)
                if country_data:
                    all_data[item] = country_data
                    print(f"  Processed {item}")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)
    print(f"Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
