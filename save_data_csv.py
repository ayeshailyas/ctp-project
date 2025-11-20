from pyalex import Topics, Funders, Works, config
from typing import List, Dict
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

config.email = os.getenv('OPENALEX_EMAIL', 'arunsisarrancs@gmail.com')

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


def get_fields_in_domain(domain_id: int = 3) -> List[Dict]:
    print("Fetching fields...")
    try:
        grouped_results = Topics().filter(**{'domain.id': domain_id}).group_by('field.id').get()
        
        fields_list = []
        for group in grouped_results:
            if group.get('key') and group.get('key_display_name'):
                fields_list.append({
                    'id': group['key'].split('/')[-1], 
                    'name': group['key_display_name'],
                    'topics_count': group['count']
                })
        
        return sorted(fields_list, key=lambda x: x['name'])

    except Exception as e:
        print(f"Error in get_fields_in_domain: {e}")
        return []


def get_top_subfields_in_domain_by_us_works(domain_id: int = 3, top_n: int = 10) -> List[Dict]:
    print("Fetching top US subfields (All Time)...")
    try:
        grouped_results = Works().filter(
            **{
                'topics.domain.id': domain_id,
                'authorships.institutions.country_code': 'US'
            }
        ).group_by('topics.subfield.id').get()
        
        subfields_list = []
        for group in grouped_results:
            if group.get('key') and group.get('key_display_name'):
                subfields_list.append({
                    'id': group['key'].split('/')[-1], 
                    'name': group['key_display_name'],
                    'us_works_count': group['count']
                })
        
        subfields_list.sort(key=lambda x: x['us_works_count'], reverse=True)
        
        return subfields_list[:top_n]
    
    except Exception as e:
        print(f"Error in get_top_subfields_in_domain_by_us_works: {e}")
        return []


def get_top_topics_in_domain_by_us_works(domain_id: int = 3, top_n: int = 10) -> List[Dict]:
    print("Fetching top US topics (All Time)...")
    try:
        grouped_results = Works().filter(
            **{
                'topics.domain.id': domain_id,
                'authorships.institutions.country_code': 'US'
            }
        ).group_by('topics.id').get()
        
        topics_list = []
        for group in grouped_results:
            if group.get('key') and group.get('key_display_name'):
                topic_id = group['key'].split('/')[-1]
                
                try:
                    # We skip detailed fetching here to save time in the main loop
                    # field_name = ... 
                    field_name = 'Unknown'
                except:
                    field_name = 'Unknown'
                
                topics_list.append({
                    'id': topic_id,
                    'name': group['key_display_name'],
                    'field': field_name,
                    'us_works_count': group['count']
                })
        
        topics_list.sort(key=lambda x: x['us_works_count'], reverse=True)
        return topics_list[:top_n]
    
    except Exception as e:
        print(f"Error in get_top_topics_in_domain_by_us_works: {e}")
        return []


def get_top_us_funder_for_subfield(subfield_id: str, subfield_name: str) -> Dict:
    print(f"  Fetching top funder for {subfield_name}...")
    try:
        grouped_results = Works().filter(**{
            'topics.subfield.id': subfield_id,
            'authorships.institutions.country_code': 'US'
        }).group_by('grants.funder').get()
        
        if not grouped_results:
            return None
        
        top_funder = None
        max_works = 0
        
        for group in grouped_results:
            if group.get('key') and group.get('key_display_name'):
                works_count = group['count']
                if works_count > max_works:
                    max_works = works_count
                    funder_id = group['key'].split('/')[-1]
                    top_funder = {
                        'subfield_id': subfield_id,
                        'subfield_name': subfield_name,
                        'funder_id': funder_id,
                        'funder_name': group['key_display_name'],
                        'subfield_works_count': works_count,
                        'total_works_count': 0,
                        'country_code': 'Unknown'
                    }
        return top_funder
    
    except Exception as e:
        print(f"  Error in get_top_us_funder_for_subfield: {e}")
        return None


def get_top_topics_for_subfields(domain_id: int = 3, top_n_subfields: int = 10, top_n_topics: int = 20):
    try:
        print("Fetching top US subfields...")
        top_subfields = get_top_subfields_in_domain_by_us_works(domain_id, top_n_subfields)
        
        if not top_subfields:
            return {}
        
        subfield_topics = {}
        for i, subfield in enumerate(top_subfields, 1):
            subfield_id = subfield['id']
            subfield_name = subfield['name']
            
            print(f"[{i}/{len(top_subfields)}] Fetching top topics for: {subfield_name}")
            
            grouped_results = Works().filter(
                **{
                    'topics.domain.id': domain_id,
                    'topics.subfield.id': subfield_id,
                    'authorships.institutions.country_code': 'US'
                }
            ).group_by('topics.id').get()
            
            topics_list = []
            for group in grouped_results:
                if group.get('key') and group.get('key_display_name'):
                    topic_info = group.get('primary_topic', {})
                    field_name = topic_info.get('field', {}).get('display_name', 'Unknown')
                    subfield_name_from_topic = topic_info.get('subfield', {}).get('display_name', 'Unknown')
                    
                    topics_list.append({
                        'id': group['key'].split('/')[-1],
                        'name': group['key_display_name'],
                        'field': field_name,
                        'subfield': subfield_name_from_topic,
                        'us_works_count': group['count']
                    })
            
            topics_list.sort(key=lambda x: x['us_works_count'], reverse=True)
            subfield_topics[subfield_id] = topics_list[:top_n_topics]
        
        return subfield_topics
    except Exception as e:
        print(f"Error in get_top_topics_for_subfields: {e}")
        return {}


# --- NEW FUNCTION FOR YEARLY TRENDS ---
def fetch_yearly_trends(domain_id=3, years_back=20):
    """
    Loops through each year from (Current - years_back) to Current.
    1. Gets Top 10 Subfields for that specific year.
    2. For each of those subfields, gets Top 20 Topics for that specific year.
    3. Saves to 'yearly_subfields.csv' and 'yearly_subfield_topics.csv'.
    """
    current_year = datetime.now().year
    start_year = current_year - years_back
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    all_yearly_subfields = []
    all_yearly_topics = []

    print("\n" + "=" * 80)
    print(f"FETCHING YEARLY DATA ({start_year} - {current_year})")
    print("=" * 80)

    for year in range(start_year, current_year + 1):
        print(f"\nProcessing Year: {year}")
        
        # 1. Get Top 10 Subfields for THIS YEAR
        try:
            subfields_result = Works().filter(
                **{
                    'topics.domain.id': domain_id,
                    'authorships.institutions.country_code': 'US',
                    'publication_year': year
                }
            ).group_by('topics.subfield.id').get()
            
            # Parse results
            year_subfields = []
            for group in subfields_result:
                if group.get('key') and group.get('key_display_name'):
                    year_subfields.append({
                        'year': year,
                        'id': group['key'].split('/')[-1], 
                        'name': group['key_display_name'],
                        'us_works_count': group['count']
                    })
            
            # Sort and keep top 10
            year_subfields.sort(key=lambda x: x['us_works_count'], reverse=True)
            top_10_subfields = year_subfields[:10]
            all_yearly_subfields.extend(top_10_subfields)
            
            print(f"  ✓ Found {len(top_10_subfields)} subfields")

            # 2. For each top subfield, get top 20 topics for THIS YEAR
            for i, sf in enumerate(top_10_subfields):
                sf_id = sf['id']
                sf_name = sf['name']
                
                try:
                    topics_result = Works().filter(
                        **{
                            'topics.domain.id': domain_id,
                            'topics.subfield.id': sf_id,
                            'authorships.institutions.country_code': 'US',
                            'publication_year': year
                        }
                    ).group_by('topics.id').get()
                    
                    year_topics = []
                    for group in topics_result:
                        if group.get('key') and group.get('key_display_name'):
                            year_topics.append({
                                'year': year,
                                'subfield_id': sf_id,
                                'subfield_name': sf_name,
                                'id': group['key'].split('/')[-1],
                                'name': group['key_display_name'],
                                'us_works_count': group['count']
                            })
                    
                    year_topics.sort(key=lambda x: x['us_works_count'], reverse=True)
                    top_20_topics = year_topics[:20]
                    all_yearly_topics.extend(top_20_topics)
                    
                except Exception as e:
                    print(f"    x Error fetching topics for {sf_name}: {e}")
                    
        except Exception as e:
            print(f"  x Error fetching subfields for year {year}: {e}")

    # Save Consolidated CSVs
    print("\nSaving data...")
    
    if all_yearly_subfields:
        df_sf = pd.DataFrame(all_yearly_subfields)
        df_sf['fetch_date'] = timestamp
        path_sf = os.path.join(DATA_DIR, 'yearly_subfields.csv')
        df_sf.to_csv(path_sf, index=False)
        print(f"✓ Saved yearly subfields to {path_sf} ({len(df_sf)} rows)")

    if all_yearly_topics:
        df_tp = pd.DataFrame(all_yearly_topics)
        df_tp['fetch_date'] = timestamp
        path_tp = os.path.join(DATA_DIR, 'yearly_subfield_topics.csv')
        df_tp.to_csv(path_tp, index=False)
        print(f"✓ Saved yearly topics to {path_tp} ({len(df_tp)} rows)")


def main():
    domain_id = 3  # Physical Sciences
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 80)
    print(f"FETCHING DATA FROM OPENALEX API")
    print(f"Timestamp: {timestamp}")
    print("=" * 80)
    
    # 1. Basic All-Time Data (Required for other views)
    # We keep these to ensure the Globe and standard Graph views don't break
    fields = get_fields_in_domain(domain_id)
    if fields:
        pd.DataFrame(fields).to_csv(os.path.join(DATA_DIR, 'fields.csv'), index=False)
    
    top_subfields = get_top_subfields_in_domain_by_us_works(domain_id, top_n=10)
    if top_subfields:
        pd.DataFrame(top_subfields).to_csv(os.path.join(DATA_DIR, 'top_subfields_us.csv'), index=False)
        
        # Funders
        funders_data = []
        for subfield in top_subfields:
            funder = get_top_us_funder_for_subfield(subfield['id'], subfield['name'])
            if funder:
                funders_data.append(funder)
        if funders_data:
            pd.DataFrame(funders_data).to_csv(os.path.join(DATA_DIR, 'subfield_funders_us.csv'), index=False)

        # Topics (All time)
        subfield_topics_data = get_top_topics_for_subfields(domain_id, top_n_subfields=10, top_n_topics=20)
        all_topics = []
        for subfield_id, topics_list in subfield_topics_data.items():
            for topic in topics_list:
                topic['subfield_id'] = subfield_id
                all_topics.append(topic)
        if all_topics:
            pd.DataFrame(all_topics).to_csv(os.path.join(DATA_DIR, 'subfield_topics_us.csv'), index=False)
            
    # 2. NEW: Run Yearly Trend Fetcher
    # This loops 20 times (once per year)
    fetch_yearly_trends(domain_id=3, years_back=20)
    
    print("\n" + "=" * 80)
    print("DATA FETCH COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
