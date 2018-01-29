from elasticsearch import Elasticsearch
from databook import configuration as conf


base_url = conf.get('elasticsearch', 'base_url')

es = Elasticsearch([base_url])


def search_elastic(searchterm, doc_type=None, page_start=0, size=20):
    body = {
        "from" : page_start, 
        "size" : size,
        "query": {
            "bool": {
                "must": [{"match": {"name": searchterm}}]
                # "must_not": [{"match": {"description": "beta"}}],
                # "filter": [{"term": {"category": "search"}}]
            }
        }
    }

    if doc_type is not None:
        return es.search(
            index="dataportal-node", 
            doc_type=doc_type,
            body=body);

    return es.search(
        index="dataportal-node", 
        body=body);
