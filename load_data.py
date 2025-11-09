import pandas as pd
import os
from datetime import datetime


DATA_DIR = "data"


def check_data_exists():
    required_files = [
        'fields.csv',
        'top_subfields_us.csv',
        'subfield_funders_us.csv',
        'top_topics_us.csv'
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
    
    data['fields'] = pd.read_csv(os.path.join(DATA_DIR, 'fields.csv'))
    data['subfields'] = pd.read_csv(os.path.join(DATA_DIR, 'top_subfields_us.csv'))
    data['funders'] = pd.read_csv(os.path.join(DATA_DIR, 'subfield_funders_us.csv'))
    data['topics'] = pd.read_csv(os.path.join(DATA_DIR, 'top_topics_us.csv'))
    
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
    
    print("TOP 10 SUBFIELDS (by US works count):")
    print("-" * 80)
    for idx, row in data['subfields'].iterrows():
        print(f"{idx+1:2d}. {row['name']:50s} (ID: {str(row['id']):10s}) US Works: {row['us_works_count']:,}")
    
    print()
    print("=" * 80)
    
    print("TOP US FUNDER FOR EACH SUBFIELD:")
    print("-" * 80)
    for idx, row in data['funders'].iterrows():
        print(f"\n{idx+1:2d}. Subfield: {row['subfield_name']}")
        print(f"    Top US Funder: {row['funder_name']}")
        print(f"    Works in this subfield: {row['subfield_works_count']:,}")
        total = row['total_works_count']
        total_str = f"{int(total):,}" if pd.notna(total) and total != 0 else "N/A"
        print(f"    Total works funded: {total_str} | Country: {row['country_code']}")
    
    print()
    print("=" * 80)
    
    print("TOP 10 TOPICS (by US works count):")
    print("-" * 80)
    for idx, row in data['topics'].iterrows():
        print(f"{idx+1:2d}. {row['name']:50s}")
        print(f"     Field: {row['field']}")
        print(f"     ID: {str(row['id']):10s} | US Works: {row['us_works_count']:,}")
        print()


def get_subfield_info(data, subfield_name):
    subfield = data['subfields'][data['subfields']['name'].str.contains(subfield_name, case=False)]
    
    if subfield.empty:
        print(f"No subfield found matching '{subfield_name}'")
        return None
    
    subfield = subfield.iloc[0]
    funder = data['funders'][data['funders']['subfield_id'] == subfield['id']]
    
    print(f"\nSubfield: {subfield['name']}")
    print(f"ID: {subfield['id']}")
    print(f"US Works Count: {subfield['us_works_count']:,}")
    
    if not funder.empty:
        funder = funder.iloc[0]
        print(f"\nTop US Funder: {funder['funder_name']}")
        print(f"Works in this subfield: {funder['subfield_works_count']:,}")
        print(f"Total works funded: {funder['total_works_count']:,}")
        print(f"Country: {funder['country_code']}")
    
    return subfield


def get_topic_info(data, topic_name):
    topic = data['topics'][data['topics']['name'].str.contains(topic_name, case=False)]
    
    if topic.empty:
        print(f"No topic found matching '{topic_name}'")
        return None
    
    topic = topic.iloc[0]
    
    print(f"\nTopic: {topic['name']}")
    print(f"ID: {topic['id']}")
    print(f"Field: {topic['field']}")
    print(f"US Works Count: {topic['us_works_count']:,}")
    
    return topic


def main():
    if not check_data_exists():
        return
    
    print("Loading data from CSV files...")
    data = load_all_data()
    print(f"✓ Data loaded successfully!\n")
    
    display_summary(data)
    
if __name__ == "__main__":
    main()
