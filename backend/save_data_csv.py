from pyalex import Topics, Works, config
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import random

# Load environment variables
load_dotenv()
config.email = os.getenv('OPENALEX_EMAIL', 'arunsisarrancs@gmail.com')

# --- CONFIGURATION ---
DATA_DIR = "data"

# If None, it will fetch the Top 100 countries by volume and process ALL of them.
# Example: TARGET_COUNTRIES = ['US', 'CN', 'MX', 'BR', 'NG'] 
TARGET_COUNTRIES = None 

# How many years back to track for the yearly trends
YEARS_BACK = 20

# Max retries for API calls
MAX_RETRIES = 10

def safe_get(query_object):
    """
    Wraps the pyalex .get() method with a custom retry loop 
    specifically designed to handle 429 (Too Many Requests) errors.
    """
    for attempt in range(MAX_RETRIES):
        try:
            return query_object.get()
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "connection" in error_str:
                wait_time = (2 ** attempt) + random.uniform(0, 1) # Exponential backoff
                if attempt > 2:
                    print(f"    [!] API Limit Hit (429). Pausing for {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"    [!] Unexpected Error: {e}")
                return []
    
    print(f"    [X] Failed after {MAX_RETRIES} attempts.")
    return []

def get_active_countries(limit: int = 100) -> List[Dict]:
    """
    Fetches the top countries by work count.
    """
    print(f"Fetching list of top {limit} active countries...")
    try:
        groups = safe_get(Works().group_by('authorships.institutions.country_code'))
        
        countries = []
        for g in groups:
            if g.get('key'):
                raw_key = g['key']
                code = raw_key.split('/')[-1] if 'openalex.org' in raw_key else raw_key
                
                countries.append({
                    'code': code,
                    'name': g['key_display_name'],
                    'count': g['count']
                })
        
        return countries[:limit]
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return []

def get_top_subfields_all_domains(country_code: str, top_n: int = 10) -> List[Dict]:
    """
    Get All-Time Top Subfields for a specific country ACROSS ALL DOMAINS.
    """
    try:
        # Note: We removed the 'topics.domain.id' filter
        query = Works().filter(
            **{
                'authorships.institutions.country_code': country_code
            }
        ).group_by('topics.subfield.id')
        
        grouped = safe_get(query)
        
        results = []
        for g in grouped:
            if g.get('key'):
                results.append({
                    'id': g['key'].split('/')[-1],
                    'name': g['key_display_name'],
                    'works_count': g['count']
                })
        results.sort(key=lambda x: x['works_count'], reverse=True)
        return results[:top_n]
    except Exception as e:
        print(f"  [!] Error fetching top subfields for {country_code}: {e}")
        return []

def fetch_yearly_trends_for_country(country_code: str, country_name: str):
    """
    Fetches yearly stats ONLY for the subfields that are in the All-Time Top 10.
    """
    current_year = datetime.now().year
    start_year = current_year - YEARS_BACK
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    country_dir = os.path.join(DATA_DIR, country_code)
    os.makedirs(country_dir, exist_ok=True)
    
    print(f"\n  > Starting Cross-Domain Analysis for {country_name} ({country_code})...")
    
    # 1. First, find out WHO the top 10 are (All-Time, All-Domains)
    top_sf_data = get_top_subfields_all_domains(country_code, top_n=10)
    top_sf_ids = [item['id'] for item in top_sf_data]
    
    if not top_sf_ids:
        print("    x No subfields found. Skipping.")
        return

    # Save the All-Time Top 10 list first
    pd.DataFrame(top_sf_data).to_csv(os.path.join(country_dir, 'top_subfields_all_time.csv'), index=False)

    all_yearly_data = []

    # 2. Iterate through years to get history for these specific subfields
    for year in range(start_year, current_year + 1):
        # We filter by the specific subfield IDs we just found
        ids_string = "|".join(top_sf_ids)
        
        sf_query = Works().filter(
            **{
                'authorships.institutions.country_code': country_code,
                'publication_year': year,
                'topics.subfield.id': ids_string
            }
        ).group_by('topics.subfield.id')
        
        sf_groups = safe_get(sf_query)
        
        if not sf_groups:
            continue

        for g in sf_groups:
            if g.get('key'):
                all_yearly_data.append({
                    'year': year,
                    'id': g['key'].split('/')[-1],
                    'name': g['key_display_name'],
                    'works_count': g['count'],
                    'country': country_code
                })
        
        time.sleep(0.1)

    # Save Yearly Trends
    if all_yearly_data:
        df = pd.DataFrame(all_yearly_data)
        df['fetch_date'] = timestamp
        df.to_csv(os.path.join(country_dir, 'yearly_subfields.csv'), index=False)
        
    print(f"    ✓ Saved data to {country_dir}/")

def main():
    # 1. Determine which countries to process
    if TARGET_COUNTRIES:
        country_list = [{'code': c, 'name': c} for c in TARGET_COUNTRIES]
    else:
        # Fetch top 50 active countries
        country_list = get_active_countries(limit=100) 
    
    print("=" * 60)
    print(f"PROCESSING {len(country_list)} COUNTRIES (ALL DOMAINS)")
    print("=" * 60)

    for i, country in enumerate(country_list, 1):
        code = country['code']
        name = country['name']
        
        print(f"\n[{i}/{len(country_list)}] Processing Country: {name} ({code})")
        
        try:
            fetch_yearly_trends_for_country(code, name)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"CRITICAL ERROR on {name}: {e}")
            continue

    print("\n" + "="*60)
    print("ALL JOBS COMPLETE")

if __name__ == "__main__":
    main()
