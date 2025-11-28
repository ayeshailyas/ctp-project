import os
import pandas as pd
import json

# Configuration
DATA_DIR = "data"
OUTPUT_FILE = "src/data/generated-data.json"

def get_global_averages(data_dir):
    """
    Pass 1: Sum up works from ALL countries to find the 'Global Standard'.
    Returns:
        global_subfield_volumes: {'Artificial Intelligence': 500000, ...}
        total_global_works: 15000000
    """
    print("  Calculating global averages...")
    global_subfield_volumes = {}
    total_global_works = 0
    
    if os.path.exists(data_dir):
        for item in os.listdir(data_dir):
            subfields_file = os.path.join(data_dir, item, "top_subfields_all_time.csv")
            if os.path.exists(subfields_file):
                try:
                    df = pd.read_csv(subfields_file)
                    # Sum up volumes
                    for _, row in df.iterrows():
                        name = row['name']
                        count = row['works_count']
                        
                        global_subfield_volumes[name] = global_subfield_volumes.get(name, 0) + count
                        total_global_works += count
                except:
                    pass
                    
    return global_subfield_volumes, total_global_works

def get_country_stats(country_code, global_volumes, global_total):
    country_path = os.path.join(DATA_DIR, country_code)
    
    subfields_file = os.path.join(country_path, "top_subfields_all_time.csv")
    yearly_subfields_file = os.path.join(country_path, "yearly_subfields.csv")
    
    stats = {
        "countryCode": country_code,
        "countryName": country_code,
        "topSubfields": [],
        "uniqueSubfields": [], # <--- NEW SECTION
        "trends": {}
    }

    # 1. Process Top Subfields & Calculate Uniqueness
    top_names = []
    if os.path.exists(subfields_file):
        try:
            df = pd.read_csv(subfields_file)
            
            # A. Basic Top 10 (Volume)
            top_10 = df.head(10).rename(columns={'name': 'name', 'works_count': 'totalWorks'})
            stats["topSubfields"] = top_10[['name', 'totalWorks']].to_dict('records')
            top_names = top_10['name'].tolist()

            # B. Calculate Uniqueness (RCA Score)
            # Formula: (Country_Share_of_Topic) / (Global_Share_of_Topic)
            country_total_works = df['works_count'].sum()
            
            uniqueness_list = []
            for _, row in df.iterrows():
                topic_name = row['name']
                topic_vol = row['works_count']
                
                # 1. How much does THIS country care about this topic?
                country_share = topic_vol / country_total_works if country_total_works > 0 else 0
                
                # 2. How much does the WORLD care about this topic?
                world_vol = global_volumes.get(topic_name, 0)
                world_share = world_vol / global_total if global_total > 0 else 1
                
                # 3. The Score (Higher = More Unique to this country)
                # Avoid divide by zero
                if world_share == 0: world_share = 0.00001
                score = country_share / world_share
                
                uniqueness_list.append({
                    'name': topic_name,
                    'totalWorks': topic_vol,
                    'score': round(score, 2)
                })
            
            # Sort by SCORE (Highest first) and take top 5
            uniqueness_list.sort(key=lambda x: x['score'], reverse=True)
            stats["uniqueSubfields"] = uniqueness_list[:5]

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
    print("Generating interactive JSON data with Uniqueness Scores...")
    
    # PASS 1: Calculate Global Totals
    global_volumes, global_total = get_global_averages(DATA_DIR)
    print(f"  ✓ Global analysis complete ({global_total:,} total works processed)")
    
    # PASS 2: Process Each Country
    all_data = {}
    if os.path.exists(DATA_DIR):
        for item in os.listdir(DATA_DIR):
            if os.path.isdir(os.path.join(DATA_DIR, item)):
                # Pass the global stats into the function
                country_data = get_country_stats(item, global_volumes, global_total)
                if country_data:
                    all_data[item] = country_data
                    print(f"  Processed {item}")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)
    print(f"Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
