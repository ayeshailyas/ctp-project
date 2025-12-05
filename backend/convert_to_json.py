import os
import pandas as pd
import json

# Configuration
DATA_DIR = "data"
OUTPUT_FILE = "src/data/generated-data.json"

def get_global_averages(data_dir):
    print("  Calculating global averages...")
    global_subfield_volumes = {}
    total_global_works = 0
    
    if os.path.exists(data_dir):
        for item in os.listdir(data_dir):
            subfields_file = os.path.join(data_dir, item, "top_subfields_all_time.csv")
            if os.path.exists(subfields_file):
                try:
                    df = pd.read_csv(subfields_file)
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
    top_works_file = os.path.join(country_path, "top_works.csv") # <--- NEW FILE
    
    stats = {
        "countryCode": country_code,
        "countryName": country_code,
        "topSubfields": [],
        "uniqueSubfields": [], 
        "trends": {}
    }

    # Helper: Load Top Papers Map
    papers_map = {} # { "Subfield Name": [ {paper1}, {paper2} ] }
    if os.path.exists(top_works_file):
        try:
            works_df = pd.read_csv(top_works_file)
            # Group by subfield name
            for sf_name, group in works_df.groupby('subfield_name'):
                # Convert top 3 papers to list of dicts
                papers = group[['title', 'doi', 'year', 'cited_by_count']].fillna('').to_dict('records')
                papers_map[sf_name] = papers
        except Exception as e:
            print(f"  Warning: could not read top works for {country_code}: {e}")

    # 1. Process Top Subfields & Calculate Uniqueness
    top_names = []
    if os.path.exists(subfields_file):
        try:
            df = pd.read_csv(subfields_file)
            
            # A. Basic Top 10 (Volume)
            top_10 = df.head(10).rename(columns={'name': 'name', 'works_count': 'totalWorks'})
            top_subfields_list = top_10[['name', 'totalWorks']].to_dict('records')

            # Attach Papers to Top Subfields
            for item in top_subfields_list:
                item['topPapers'] = papers_map.get(item['name'], [])

            stats["topSubfields"] = top_subfields_list
            top_names = top_10['name'].tolist()

            # B. Calculate Uniqueness (RCA Score)
            country_total_works = df['works_count'].sum()
            
            uniqueness_list = []
            for _, row in df.iterrows():
                topic_name = row['name']
                topic_vol = row['works_count']
                
                country_share = topic_vol / country_total_works if country_total_works > 0 else 0
                world_vol = global_volumes.get(topic_name, 0)
                world_share = world_vol / global_total if global_total > 0 else 1
                
                if world_share == 0: world_share = 0.00001
                score = country_share / world_share
                
                uniqueness_list.append({
                    'name': topic_name,
                    'totalWorks': topic_vol,
                    'score': round(score, 2),
                    # Attach Papers to Unique Subfields too
                    'topPapers': papers_map.get(topic_name, []) 
                })
            
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
    print("Generating interactive JSON data with Top Papers...")
    
    global_volumes, global_total = get_global_averages(DATA_DIR)
    print(f"  ✓ Global analysis complete ({global_total:,} total works processed)")
    
    all_data = {}
    if os.path.exists(DATA_DIR):
        for item in os.listdir(DATA_DIR):
            if os.path.isdir(os.path.join(DATA_DIR, item)):
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
