from pyalex import Topics, Funders, Works, config
from typing import List, Dict
from collections import Counter

config.email = "arunsisarrancs@gmail.com"

def get_fields_in_domain(domain_id: int = 3) -> List[Dict]:
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
    """Get top topics in a domain based on US works count."""
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


def get_top_us_funder_for_subfield(subfield_id: str) -> Dict:
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
                                'id': funder_id,
                                'name': funder.get('display_name', group['key_display_name']),
                                'subfield_works_count': works_count,
                                'total_works_count': funder.get('works_count', 0),
                                'country_code': funder.get('country_code', 'Unknown')
                            }
                        else:
                            top_funder = {
                                'id': funder_id,
                                'name': group['key_display_name'],
                                'subfield_works_count': works_count,
                                'total_works_count': 'N/A',
                                'country_code': 'Unknown'
                            }
                    except:
                        top_funder = {
                            'id': funder_id,
                            'name': group['key_display_name'],
                            'subfield_works_count': works_count,
                            'total_works_count': 'N/A',
                            'country_code': 'Unknown'
                        }
        
        return top_funder
    
    except Exception as e:
        print(f"Error in get_top_us_funder_for_subfield: {e}")
        return None


if __name__ == "__main__":
    domain_id = 3  # Physical Sciences
    
    print("=" * 80)
    print(f"ANALYSIS OF DOMAIN {domain_id}: PHYSICAL SCIENCES (United States Focus)")
    print("=" * 80)
    print()
    
    # Get all fields
    print("ALL FIELDS IN DOMAIN (Global):")
    print("-" * 80)
    fields = get_fields_in_domain(domain_id)
    
    for i, field in enumerate(fields, 1):
        print(f"{i:2d}. {field['name']:40s} (ID: {field['id']:10s}) Topics: {field['topics_count']:,}")
    
    print()
    print("=" * 80)
    
    print("TOP 10 SUBFIELDS (by US works count):")
    print("-" * 80)
    top_subfields = get_top_subfields_in_domain_by_us_works(domain_id, top_n=10)
    
    for i, subfield in enumerate(top_subfields, 1):
        print(f"{i:2d}. {subfield['name']:50s} (ID: {subfield['id']:10s}) US Works: {subfield['us_works_count']:,}")
    
    print()
    print("=" * 80)
    
    print("TOP US FUNDER FOR EACH SUBFIELD:")
    print("-" * 80)
    
    for i, subfield in enumerate(top_subfields, 1):
        print(f"\n{i:2d}. Subfield: {subfield['name']}")
        top_funder = get_top_us_funder_for_subfield(subfield['id'])
        
        if top_funder:
            print(f"    Top US Funder: {top_funder['name']}")
            print(f"    Works in this subfield: {top_funder['subfield_works_count']:,}")
            print(f"    Total works funded: {top_funder['total_works_count']:,} | Country: {top_funder['country_code']}")
        else:
            print(f"    No US funder data available")
    
    print()
    print("=" * 80)
    
    print("TOP 10 TOPICS (by US works count):")
    print("-" * 80)
    top_topics = get_top_topics_in_domain_by_us_works(domain_id, top_n=10)
    
    for i, topic in enumerate(top_topics, 1):
        print(f"{i:2d}. {topic['name']:50s}")
        print(f"     Field: {topic['field']}")
        print(f"     ID: {topic['id']:10s} | US Works: {topic['us_works_count']:,}")
        print()
