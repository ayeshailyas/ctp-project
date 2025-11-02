from pyalex import Works, Topics, Funders, config
from collections import Counter
import pandas as pd
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

if __name__ == "__main__":
    results = find_research_areas("Biology")

    for result in results:
        print(result)

