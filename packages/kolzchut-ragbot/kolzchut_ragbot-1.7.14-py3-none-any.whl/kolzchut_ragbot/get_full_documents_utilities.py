from elasticsearch import Elasticsearch
from typing import List, Dict, Any


def find_page_id_in_all_indices(page_id: int, es_client: Elasticsearch, indices: List[str]) -> List[Dict[str, Any]]:
    """
    Search all provided indices using the given es_client for documents with the given page_id.
    Returns a list of all matching documents' _source fields.
    """
    all_docs = []
    fixed_indicies =  ["_".join(index.split("_")[1:]) for index in indices]
    for index in fixed_indicies:
        resp = es_client.search(index=index, body={
            "query": {
                "term": {"page_id": page_id}
            }
        }, size=100)
        hits = resp.get('hits', {}).get('hits', [])
        for doc in hits:
            source_with_id = dict(doc['_source'])
            source_with_id['_id'] = doc['_id']
            all_docs.append(source_with_id)
    return all_docs


def unite_docs_to_single_instance(docs: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """
    Unites a list of Elasticsearch document dicts (with the same page_id) into a single instance dict.
    - Takes metadata fields (page_id, title, url, articleType, articleContentArea, etc.) from the first document.
    - Concatenates all 'content' fields with a line break between them.
    - Returns a single dict representing the united document, or None if docs is empty.
    """
    if not docs:
        return None
    first = docs[0]
    united_content = '\n'.join([doc.get('content', '') for doc in docs if doc.get('content')])
    instance = {
        "page_id": first.get("page_id"),
        "title": first.get("title"),
        "url": first.get("url"),
        "link": first.get("url").split("/")[-1] if first.get("url") else None,
        "articleType": first.get("articleType"),
        "articleContentArea": first.get("articleContentArea"),
        "summary": first.get("summary"),
        "categories": first.get("categories"),
        "content": united_content
    }
    return instance
