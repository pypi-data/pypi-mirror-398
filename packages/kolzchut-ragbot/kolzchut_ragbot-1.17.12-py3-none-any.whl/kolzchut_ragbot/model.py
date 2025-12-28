import datetime
import logging
import os
from .Document import factory as definitions_factory

definitions_singleton = definitions_factory()
EMBEDDING_INDEX = os.getenv("ES_EMBEDDING_INDEX", "embeddings")
semantic_models = definitions_singleton.models.keys()


def index_from_page_id(page_id: int):
    """
    Generates an index name based on the page ID.

    Args:
        page_id (int): The ID of the page.

    Returns:
        str: The generated index name.
    """
    index_postfix = round(page_id / 1000)
    return EMBEDDING_INDEX + "_" + str(index_postfix)


def create_mapping():
    """
    Creates a mapping for the model in Elasticsearch.
    """
    vector_fields = {f'{semantic_model}_{name}_vectors': {"type": "dense_vector", "dims": 1024}
                     for name, semantic_model in definitions_singleton.models.items()}

    data_fields = {}
    for field in definitions_singleton.saved_fields.keys():
        field_type = definitions_singleton.saved_fields[field]
        field_mapping = {"type": field_type}
        if field_type == "date":
            field_mapping["format"] = "yyyyMMddHHmmss"
        data_fields[f"{field}"] = field_mapping

    mappings = {
        "properties": {
            "last_update": {
                "type": "date",
            },
            **vector_fields,
            **data_fields,
        }
    }
    return mappings


class Model:
    """
    Represents the model for creating, updating, and searching documents in Elasticsearch.

    Attributes:
        custom_result_selection_function (callable): A custom function for selecting search results.
        es_client: The Elasticsearch client instance.

    Methods:
        create_index():
            Creates an index for the model in Elasticsearch.

        create_or_update_documents(paragraphs_dicts: list[dict], update=False):
            Creates or updates documents in the Elasticsearch index.

        search(embedded_search: dict[str, list[float]], size=50) -> dict[str, list[dict]]:
            Searches for similar documents using cosine similarity.
    """

    custom_result_selection_function = None

    def __init__(self, es_client, custom_result_selection_function=None):
        """
        Initializes the Model instance.

        Args:
            es_client: The Elasticsearch client instance.
            custom_result_selection_function (callable, optional): A custom function for selecting search results.
        """
        self.es_client = es_client
        if custom_result_selection_function is not None:
            self.custom_result_selection_function = custom_result_selection_function

    def create_index(self, index_name):
        """
        Creates an index for the model in Elasticsearch.
        """
        mapping = create_mapping()
        if not self.es_client.indices.exists(index=index_name):
            self.es_client.indices.create(
                index=index_name,
                mappings=mapping
            )

    def create_or_update_documents(self, paragraphs_dicts: list[dict], update=False):
        """
        Creates or updates documents in the Elasticsearch index.

        Args:
            paragraphs_dicts (list[dict]): A list of dictionaries representing the paragraphs to be indexed.
            update (bool, optional): Whether to update existing documents. Default is False.
        """

        identifier = definitions_singleton.identifier
        print(f"Creating or updating documents in the index, {len(paragraphs_dicts)} paragraphs\n")
        # Identify the doc from the first paragraph - all paragraphs should have the same doc_id
        doc_id = paragraphs_dicts[0][identifier]
        index = index_from_page_id(int(doc_id))

        if update:
            try:
                query = {
                    "query": {
                        "match": {
                            f"{identifier}": doc_id
                        }
                    }
                }
                self.es_client.delete_by_query(index=f"{EMBEDDING_INDEX}*", body=query)

            except Exception as e:
                logging.error(f"Error while searching for existing document: {e}")
        self.create_index(index)
        for i, doc_dict in enumerate(paragraphs_dicts):
            print(f"saving paragraph {i + 1} / {len(paragraphs_dicts)}")
            doc = {
                "last_update": datetime.datetime.now(),
                **doc_dict
            }

            self.es_client.index(index=index, body=doc)

    def search(self, embedded_search: dict[str, list[float]], size=50) -> dict[str, list[dict]]:
        """
        Searches for similar documents using cosine similarity.

        Args:
            embedded_search (dict[str, list[float]]): A dictionary containing the embedded search vectors.
            size (int, optional): The number of search results to return. Default is 50.

        Returns:
            dict[str, list[dict]]: A dictionary containing the search results.
        """
        results = {}
        for semantic_model, field in definitions_singleton.models.items():
            results[field] = [] if field not in results.keys() else results[field]
            body = {
                "script_score": {
                    "query": {
                        "exists": {
                            "field": f'{field}_{semantic_model}_vectors'
                        }
                    },
                    "script": {
                        "source": f"cosineSimilarity(params.query_vector, '{field}_{semantic_model}_vectors') + 1.0",
                        "params": {
                            "query_vector": embedded_search[semantic_model]
                        }
                    }
                }
            }
            print(f"Searching for {field} using {semantic_model} on index {EMBEDDING_INDEX}\n")
            field_results = self.es_client.search(
                index=EMBEDDING_INDEX + "*",
                body={
                    "size": size,
                    "query": body
                })
            results[field] = results[field] + field_results["hits"]["hits"]

        return results


model = None


def es_client_factory(es_client) -> Model:
    global model
    if model is None:
        model = Model(es_client)
    return model
