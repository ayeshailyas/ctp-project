from pyalex import Works, Topics, Funders, config
from collections import Counter
from typing import List, Dict

config.email = "arunsisarrancs@gmail.com"

def find_research_areas(search_term, max_results:int=5):
    topics = Topics().search(search_term).get()
    results = []
    for topic in topics[:max_results]:
            results.append({
                'id': topic['id'].split('/')[-1],
                'display_name': topic['display_name'],
                'works_count': topic.get('works_count', 0),
                'cited_by_count': topic.get('cited_by_count', 0),
            })
    return results

def get_fields_in_domain(domain_id):
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

def get_subfields_in_field(field_id: str):
    try:
        grouped_results = Topics().filter(**{'field.id': field_id}).group_by('subfield.id').get()
        
        subfields_list = []
        for group in grouped_results:
            if group.get('key') and group.get('key_display_name'):
                subfields_list.append({
                    'id': group['key'].split('/')[-1], 
                    'name': group['key_display_name'],
                    'topics_count': group['count']
                })
        
        return sorted(subfields_list, key=lambda x: x['name'])
    
    except Exception as e:
        print(f"Error in get_subfields_in_field: {e}")
        return []

def get_topics_in_field(field_id: str, sort_by: str = 'works_count', top_n: int = None):
    topics_pager = Topics().filter(**{'field.id': field_id})
    all_topics = topics_pager.get()

    results = []
    for topic in all_topics:
        results.append({
            'id': topic['id'].split('/')[-1],
            'name': topic['display_name'],
            'works_count': topic.get('works_count', 0),
            'cited_by_count': topic.get('cited_by_count', 0)
        })

    if not results:
        return []

    if sort_by in results[0]:
        reverse_sort = (sort_by != 'name')
        results.sort(key=lambda x: x[sort_by], reverse=reverse_sort)
    
    if top_n:
        return results[:top_n]
    
    return results


if __name__ == "__main__":
    
    domain_id = 3 
    
    print("Fields in Domain (ID: 3 'Physical Sciences')")
    fields = get_fields_in_domain(domain_id)

    print("-" * 75)
    for i, field in enumerate(fields, 1):
        print(f"{i:2d}. {field['name']:35s} (ID: {str(field['id']):15s}) (Topics: {field['topics_count']:,})")

    field_id_to_test = "17" 
    print(f"Subfields in ID: {field_id_to_test}")
    
    subfields = get_subfields_in_field(field_id_to_test)
    
    if not subfields:
        print(f"No subfields found for Field ID: {field_id_to_test}")
    else:
        print("-" * 75)
        for i, subfield in enumerate(subfields, 1):
            print(f"{i:2d}. {subfield['name']:45s} (ID: {subfield['id']:15s}) ({subfield['topics_count']})")


    print(f"Top 10 Topics ID: {field_id_to_test}")
    
    try:
        top_topics = get_topics_in_field(field_id_to_test, 
                                         sort_by='works_count', 
                                         top_n=10)
        if not top_topics:
            print(f"No topics found for Field ID: {field_id_to_test}")
        else:
            print("-" * 75)
            for i, topic in enumerate(top_topics, 1):
                print(f"{i:2d}. {topic['name']:45s} (ID: {topic['id']:15s}) ({topic['works_count']:,})")
    
    except Exception as e:
        print(f"Could not fetch topics for ID {field_id_to_test}: {e}")
