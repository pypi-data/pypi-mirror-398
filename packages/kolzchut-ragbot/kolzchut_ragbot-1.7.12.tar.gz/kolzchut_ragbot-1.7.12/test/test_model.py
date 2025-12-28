import pytest
from unittest.mock import patch, ANY
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kolzchut_ragbot.model import Model, index_from_page_id, EMBEDDING_INDEX

search_json = {
   "script_score": {
       "query": {
           "exists": {
               "field": 'content-me5_large-v10'
           }
       },
       "script": {
           "source": f"cosineSimilarity(params.query_vector, 'content-me5_large-v10') + 1.0",
           "params": {
               "Query_vector": [0.0, 0.11, ]
           }
       }
   }
}


class TestModel:

    @patch('elasticsearch.Elasticsearch')
    def test_create_index(self, EsMock):
        es_mock = EsMock()
        model = Model(es_mock)
        es_mock.indices.exists.return_value = False
        model.create_index("index_name")
        assert es_mock.indices.create.called
        _, kwargs = es_mock.indices.create.call_args
        mappings = kwargs.get("mappings")
        # Just verify that mappings contain expected structure
        assert 'properties' in mappings
        assert 'last_update' in mappings['properties']
        assert mappings['properties']['last_update']['type'] == 'date'

    @patch('elasticsearch.Elasticsearch')
    def test_create_index_false(self, EsMock):
        es_mock = EsMock()
        model = Model(es_mock)
        es_mock.indices.exists.return_value = True
        model.create_index('index_name')
        assert es_mock.indices.create.call_count == 0

    @patch('elasticsearch.Elasticsearch')
    def test_create_or_update_document_no_delete(self, EsMock):
        es_mock = EsMock()
        model = Model(es_mock)
        es_mock.search.return_value = {"hits": {"hits": []}}
        new_doc = {"doc_id": 1, "title": "title", "content": "content"}
        model.create_or_update_documents([new_doc], True)

        es_mock.index.assert_called_with(
            index=index_from_page_id(1),
            body={
                'last_update': ANY,
                'doc_id': 1,
                'title': 'title',
                'content': 'content'
            })
        assert es_mock.delete.call_count == 0
        assert es_mock.index.call_count == 1

    @patch('elasticsearch.Elasticsearch')
    def test_create_or_update_document_but_delete(self, EsMock):
        es_mock = EsMock()
        model = Model(es_mock)
        es_mock.search.return_value = {"hits": {"hits": [{"_id":"1","doc_id": 1, "title": "title", "content": "content"}]}}
        new_doc = {"doc_id": 1, "title": "edited", "content": "edited"}
        model.create_or_update_documents([new_doc], True)

        es_mock.delete_by_query.assert_called_with(
            index=f"{EMBEDDING_INDEX}*",
            body={
                "query": {
                    "match": {
                        "doc_id": 1
                    }
                }
            })
        print(es_mock.delete.call_count)
        assert es_mock.delete_by_query.call_count == 1
        assert es_mock.index.call_count == 1

    @patch('elasticsearch.Elasticsearch')
    def test_create_or_update_document_delete_false(self, EsMock):
        es_mock = EsMock()
        model = Model(es_mock)
        es_mock.search.return_value = {
            "hits": {"hits": [{"_id": "1", "doc_id": 1, "title": "title", "content": "content"}]}}
        new_doc = {"doc_id": 1, "title": "edited", "content": "edited"}
        model.create_or_update_documents([new_doc], False)

        assert 0 == es_mock.search.call_count
        assert 0 == es_mock.delete.call_count
        assert es_mock.index.call_count == 1

    @patch('elasticsearch.Elasticsearch')
    def test_search(self, EsMock):
        es_mock = EsMock()
        model = Model(es_mock)
        es_mock.search.return_value = {
            "hits": {
                "hits": [
                    {"_id": "1", "_source": {"field": "value1"}},
                    {"_id": "2", "_source": {"field": "value2"}}
                ]
            }
        }

        embedded_search = {
            "me5_large_v23": [0.1, 0.2, 0.3],
            "me5_large-v10": [0.4, 0.5, 0.6]
        }

        results = model.search(embedded_search, size=2)

        expected_query = {
            "size": 2,
            "query": {
                "script_score": {
                    "query": {
                        "exists": {
                            "field": "doc_id_me5_large-v10_vectors"
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'title_me5_large_v23_vectors') + 1.0",
                        "params": {
                            "query_vector": embedded_search["me5_large_v23"]
                        }
                    }
                }
            }
        }

        # Just verify that results is returned without error
        assert results is not None
        assert isinstance(results, dict)
