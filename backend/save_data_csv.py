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
# If a list, it will ONLY process these specific codes.
TARGET_COUNTRIES = None 
# Example: TARGET_COUNTRIES = ['US', 'CN', 'MX', 'GB', 'FR', 'JP', 'IN']

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
            # Check for 429 or connection errors
            if "429" in error_str or "connection" in error_str:
                wait_time = (2 ** attempt) + random.uniform(0, 1) # Exponential backoff
                if attempt > 2:
                    print(f"    [!] API Limit Hit (429). Pausing for {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                # If it's a different error (e.g., 404, 500), raise it immediately
                print(f"    [!] Unexpected Error: {e}")
                return []
    
    print(f"    [X] Failed after {MAX_RETRIES} attempts.")
    return []

def get_active_countries(limit: int = 100) -> List[Dict]:
    """
    Fetches the top countries by work count.
    Cleans the ID to ensure we get 'US' instead of 'https://openalex.org/countries/US'.
    """
    print(f"Fetching list of top {limit} active countries...")
    try:
        groups = safe_get(Works().group_by('authorships.institutions.country_code'))
        
        countries = []
        for g in groups:
            if g.get('key'):
                # CLEANING STEP: Strip URL if present
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

def get_top_subfields(country_code: str, domain_id: int = 3, top_n: int = 10) -> List[Dict]:
    """Get All-Time Top Subfields for a specific country."""
    try:
        query = Works().filter(
            **{
                'topics.domain.id': domain_id,
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

def fetch_yearly_trends_for_country(country_code: str, country_name: str, domain_id: int = 3):
    """
    Fetches yearly stats ONLY for the subfields that are in the All-Time Top 10.
    This ensures the graphs never cut off.
    """
    current_year = datetime.now().year
    start_year = current_year - YEARS_BACK
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    country_dir = os.path.join(DATA_DIR, country_code)
    os.makedirs(country_dir, exist_ok=True)
    
    print(f"\n  > Starting Yearly Analysis for {country_name} ({country_code})...")
    
    # 1. First, find out WHO the top 10 are (All-Time)
    top_sf_data = get_top_subfields(country_code, domain_id, top_n=10)
    top_sf_ids = [item['id'] for item in top_sf_data] # ["subfield-id-1", "subfield-id-2", ...]
    
    if not top_sf_ids:
        print("    x No subfields found. Skipping.")
        return

    all_yearly_data = []

    # 2. Iterate through years
    for year in range(start_year, current_year + 1):
        # Instead of asking "What is popular this year?", we ask:
        # "How did our Top 10 specific subfields perform in this year?"
        
        # We can filter by the specific subfield IDs using the pipe | operator (OR)
        # OpenAlex API allows: topics.subfield.id:id1|id2|id3
        ids_string = "|".join(top_sf_ids)
        
        sf_query = Works().filter(
            **{
                'topics.domain.id': domain_id,
                'authorships.institutions.country_code': country_code,
                'publication_year': year,
                'topics.subfield.id': ids_string # <--- CRITICAL CHANGE
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
        
        # Small sleep to be polite
        time.sleep(0.1)

    # Save to CSV
    if all_yearly_data:
        df = pd.DataFrame(all_yearly_data)
        df['fetch_date'] = timestamp
        # We overwrite the old file
        df.to_csv(os.path.join(country_dir, 'yearly_subfields.csv'), index=False)
        
    print(f"    ✓ Saved {len(all_yearly_data)} rows (All-Time Top 10 History) to {country_dir}/")

def main():
    domain_id = 3 # Physical Sciences
    
    # 1. Determine which countries to process
    if TARGET_COUNTRIES:
        # Create dummy dicts if user provided specific list
        country_list = [{'code': c, 'name': c} for c in TARGET_COUNTRIES]
    else:
        # Fetch top 50 to avoid taking too long. Increase limit if needed.
        country_list = get_active_countries(limit=50) 
    
    print("=" * 60)
    print(f"PROCESSING {len(country_list)} COUNTRIES")
    print("=" * 60)

    for i, country in enumerate(country_list, 1):
        code = country['code']
        name = country['name']
        
        print(f"\n[{i}/{len(country_list)}] Processing Country: {name} ({code})")
        
        try:
            # A. Standard All-Time Stats (Fast)
            top_sf = get_top_subfields(code, domain_id)
            if top_sf:
                country_dir = os.path.join(DATA_DIR, code)
                os.makedirs(country_dir, exist_ok=True)
                pd.DataFrame(top_sf).to_csv(os.path.join(country_dir, 'top_subfields_all_time.csv'), index=False)
            
            # B. Yearly Trends (Slow - The "Deep Dive")
            fetch_yearly_trends_for_country(code, name, domain_id)
            
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
