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

# Set to None to fetch ALL available countries
TARGET_COUNTRIES = None 

# How many years back to track for the yearly trends
YEARS_BACK = 20

# Max retries for API calls
MAX_RETRIES = 10

def safe_get(query_object, **kwargs):
    """
    Wraps the pyalex .get() method with a custom retry loop.
    Now accepts **kwargs to pass arguments (like per_page) to .get()
    """
    for attempt in range(MAX_RETRIES):
        try:
            return query_object.get(**kwargs)
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

def get_active_countries(limit: Optional[int] = None) -> List[Dict]:
    """
    Fetches the top countries by work count. 
    If limit is None, fetches ALL countries found in OpenAlex.
    """
    label = f"top {limit}" if limit else "ALL"
    print(f"Fetching list of {label} active countries...")
    
    try:
        # Group by country code to get the list of all active countries
        groups = safe_get(Works().group_by('authorships.institutions.country_code'))
        
        countries = []
        for g in groups:
            if g.get('key'):
                raw_key = g['key']
                # Clean up key (handle urls like https://openalex.org/US)
                code = raw_key.split('/')[-1] if 'openalex.org' in raw_key else raw_key
                
                # Filter out 'unknown' or invalid codes
                if code and code.lower() != 'unknown':
                    countries.append({
                        'code': code,
                        'name': g['key_display_name'] or code, # Fallback to code if name is missing
                        'count': g['count']
                    })
        
        # Sort by volume
        countries.sort(key=lambda x: x['count'], reverse=True)
        
        if limit:
            return countries[:limit]
        return countries
        
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return []

def get_top_subfields_all_domains(country_code: str, top_n: int = 10) -> List[Dict]:
    """
    Get All-Time Top Subfields for a specific country ACROSS ALL DOMAINS.
    """
    try:
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

def fetch_top_works_for_subfields(country_code: str, subfields: List[Dict], country_dir: str):
    """
    For each top subfield, fetch the top 3 most cited papers from the last 20 years.
    """
    print(f"    > Fetching Top 3 Papers for {len(subfields)} subfields...")
    
    current_year = datetime.now().year
    start_date = f"{current_year - YEARS_BACK}-01-01"
    
    all_top_works = []

    for sf in subfields:
        sf_id = sf['id']
        sf_name = sf['name']

        # Query: Filter by Country + Subfield + Date, Sort by Citations
        # REMOVED .per_page(3) from the chain here
        query = Works().filter(
            **{
                'authorships.institutions.country_code': country_code,
                'topics.subfield.id': sf_id,
                'from_publication_date': start_date
            }
        ).sort(cited_by_count="desc").select([
            "id", 
            "doi", 
            "title", 
            "publication_year", 
            "cited_by_count"
        ])

        # ADDED per_page=3 here
        works = safe_get(query, per_page=3)

        for w in works:
            all_top_works.append({
                'subfield_id': sf_id,
                'subfield_name': sf_name,
                'title': w.get('title'),
                'doi': w.get('doi'),
                'year': w.get('publication_year'),
                'cited_by_count': w.get('cited_by_count'),
                'id': w.get('id')
            })
        
        time.sleep(0.2)

    if all_top_works:
        df = pd.DataFrame(all_top_works)
        df.to_csv(os.path.join(country_dir, 'top_works.csv'), index=False)
        print(f"    ✓ Saved top papers to {country_dir}/top_works.csv")

def process_country(country_code: str, country_name: str):
    current_year = datetime.now().year
    start_year = current_year - YEARS_BACK
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    country_dir = os.path.join(DATA_DIR, country_code)
    os.makedirs(country_dir, exist_ok=True)
    
    print(f"\n  > Starting Analysis for {country_name} ({country_code})...")
    
    # 1. Get All-Time Top 10 Subfields
    top_sf_data = get_top_subfields_all_domains(country_code, top_n=10)
    
    if not top_sf_data:
        print("    x No subfields found. Skipping.")
        return

    # Save Top 10 list
    pd.DataFrame(top_sf_data).to_csv(os.path.join(country_dir, 'top_subfields_all_time.csv'), index=False)

    # 2. Get Yearly Trends for these subfields
    top_sf_ids = [item['id'] for item in top_sf_data]
    all_yearly_data = []

    for year in range(start_year, current_year + 1):
        ids_string = "|".join(top_sf_ids)
        sf_query = Works().filter(
            **{
                'authorships.institutions.country_code': country_code,
                'publication_year': year,
                'topics.subfield.id': ids_string
            }
        ).group_by('topics.subfield.id')
        
        sf_groups = safe_get(sf_query)
        
        if sf_groups:
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

    if all_yearly_data:
        df = pd.DataFrame(all_yearly_data)
        df['fetch_date'] = timestamp
        df.to_csv(os.path.join(country_dir, 'yearly_subfields.csv'), index=False)

    # 3. Fetch Top 3 Papers per Subfield
    fetch_top_works_for_subfields(country_code, top_sf_data, country_dir)

def main():
    # 1. Determine which countries to process
    if TARGET_COUNTRIES:
        country_list = [{'code': c, 'name': c} for c in TARGET_COUNTRIES]
    else:
        # Fetch ALL active countries (limit=None)
        country_list = get_active_countries(limit=None) 
    
    print("=" * 60)
    print(f"PROCESSING {len(country_list)} COUNTRIES")
    print("=" * 60)

    for i, country in enumerate(country_list, 1):
        code = country['code']
        name = country['name']
        
        print(f"\n[{i}/{len(country_list)}] Processing Country: {name} ({code})")
        
        try:
            process_country(code, name)
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
