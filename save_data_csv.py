from pyalex import Topics, Funders, Works, config
from typing import List, Dict
import pandas as pd
from datetime import datetime
import os

config.email = "arunsisarrancs@gmail.com"

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
    print("Fetching top US subfields...")
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
    print("Fetching top US topics...")
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
                
                # Fetch the topic to get field information
                try:
                    topic_details = Topics().filter(**{'openalex': f"https://openalex.org/{topic_id}"}).get()[0]
                    field_name = topic_details.get('field', {}).get('display_name', 'Unknown')
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
                    
                    try:
                        funder_details = Funders().filter(**{'openalex': group['key']}).get()
                        if funder_details:
                            funder = funder_details[0]
                            top_funder = {
                                'subfield_id': subfield_id,
                                'subfield_name': subfield_name,
                                'funder_id': funder_id,
                                'funder_name': funder.get('display_name', group['key_display_name']),
                                'subfield_works_count': works_count,
                                'total_works_count': funder.get('works_count', 0),
                                'country_code': funder.get('country_code', 'Unknown')
                            }
                        else:
                            top_funder = {
                                'subfield_id': subfield_id,
                                'subfield_name': subfield_name,
                                'funder_id': funder_id,
                                'funder_name': group['key_display_name'],
                                'subfield_works_count': works_count,
                                'total_works_count': 0,
                                'country_code': 'Unknown'
                            }
                    except:
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


def main():
    domain_id = 3  # Physical Sciences
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 80)
    print(f"FETCHING DATA FROM OPENALEX API - Domain {domain_id}: Physical Sciences")
    print(f"Timestamp: {timestamp}")
    print("=" * 80)
    print()
    
    fields = get_fields_in_domain(domain_id)
    if fields:
        df_fields = pd.DataFrame(fields)
        df_fields['fetch_date'] = timestamp
        csv_path = os.path.join(DATA_DIR, 'fields.csv')
        df_fields.to_csv(csv_path, index=False)
        print(f"✓ Saved {len(fields)} fields to {csv_path}")
    
    print()
    
    top_subfields = get_top_subfields_in_domain_by_us_works(domain_id, top_n=10)
    if top_subfields:
        df_subfields = pd.DataFrame(top_subfields)
        df_subfields['fetch_date'] = timestamp
        csv_path = os.path.join(DATA_DIR, 'top_subfields_us.csv')
        df_subfields.to_csv(csv_path, index=False)
        print(f"✓ Saved {len(top_subfields)} subfields to {csv_path}")
    
    print()
    
    print("Fetching top US funders for each subfield:")
    funders_data = []
    for subfield in top_subfields:
        funder = get_top_us_funder_for_subfield(subfield['id'], subfield['name'])
        if funder:
            funders_data.append(funder)
    
    if funders_data:
        df_funders = pd.DataFrame(funders_data)
        df_funders['fetch_date'] = timestamp
        csv_path = os.path.join(DATA_DIR, 'subfield_funders_us.csv')
        df_funders.to_csv(csv_path, index=False)
        print(f"✓ Saved {len(funders_data)} funder records to {csv_path}")
    
    print()
    
    top_topics = get_top_topics_in_domain_by_us_works(domain_id, top_n=10)
    if top_topics:
        df_topics = pd.DataFrame(top_topics)
        df_topics['fetch_date'] = timestamp
        csv_path = os.path.join(DATA_DIR, 'top_topics_us.csv')
        df_topics.to_csv(csv_path, index=False)
        print(f"✓ Saved {len(top_topics)} topics to {csv_path}")
    
    print()
    print("=" * 80)
    print("DATA FETCH COMPLETE!")
    print("=" * 80)
    print(f"\nAll CSV files saved to '{DATA_DIR}/' directory")
    print(f"Last updated: {timestamp}")


if __name__ == "__main__":
    main()
