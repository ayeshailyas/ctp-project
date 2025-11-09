from pyalex import Topics, config
from typing import List, Dict

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


def get_top_subfields_in_domain(domain_id: int = 3, top_n: int = 10) -> List[Dict]:
    try:
        grouped_results = Topics().filter(**{'domain.id': domain_id}).group_by('subfield.id').get()
        
        subfields_list = []
        for group in grouped_results:
            if group.get('key') and group.get('key_display_name'):
                subfields_list.append({
                    'id': group['key'].split('/')[-1], 
                    'name': group['key_display_name'],
                    'topics_count': group['count']
                })
        
        subfields_list.sort(key=lambda x: x['topics_count'], reverse=True)
        
        return subfields_list[:top_n]
    
    except Exception as e:
        print(f"Error in get_top_subfields_in_domain: {e}")
        return []


def get_top_topics_in_domain(domain_id: int = 3, top_n: int = 10) -> List[Dict]:
    try:
        # Get all topics in the domain
        topics_pager = Topics().filter(**{'domain.id': domain_id})
        all_topics = topics_pager.get()
        
        results = []
        
        for topic in all_topics:
            field_name = "Unknown"
            if topic.get('field') and topic['field'].get('display_name'):
                field_name = topic['field']['display_name']
            
            results.append({
                'id': topic['id'].split('/')[-1],
                'name': topic['display_name'],
                'field': field_name,
                'works_count': topic.get('works_count', 0),
                'cited_by_count': topic.get('cited_by_count', 0)
            })
        
        results.sort(key=lambda x: x['works_count'], reverse=True)
        
        return results[:top_n]
    
    except Exception as e:
        print(f"Error in get_top_topics_in_domain: {e}")
        return []


if __name__ == "__main__":
    domain_id = 3  
    
    print("ALL FIELDS IN DOMAIN:")
    print("-" * 80)
    fields = get_fields_in_domain(domain_id)
    
    for i, field in enumerate(fields, 1):
        print(f"{i:2d}. {field['name']:40s} (ID: {field['id']:10s}) Topics: {field['topics_count']:,}")
    
    print()
    print("=" * 80)
    
    print("TOP 10 SUBFIELDS (by number of topics):")
    print("-" * 80)
    top_subfields = get_top_subfields_in_domain(domain_id, top_n=10)
    
    for i, subfield in enumerate(top_subfields, 1):
        print(f"{i:2d}. {subfield['name']:50s} (ID: {subfield['id']:10s}) Topics: {subfield['topics_count']:,}")
    
    print()
    print("=" * 80)
    
    print("TOP 10 MOST POPULAR TOPICS (by number of papers):")
    print("-" * 80)
    top_topics = get_top_topics_in_domain(domain_id, top_n=10)
    
    for i, topic in enumerate(top_topics, 1):
        print(f"{i:2d}. {topic['name']:50s}")
        print(f"     Field: {topic['field']}")
        print(f"     ID: {topic['id']:10s} | Works: {topic['works_count']:,} | Citations: {topic['cited_by_count']:,}")
        print()
