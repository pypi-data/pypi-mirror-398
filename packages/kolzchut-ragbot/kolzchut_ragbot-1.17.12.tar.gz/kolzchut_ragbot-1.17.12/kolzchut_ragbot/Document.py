import json
import os

DEFINITIONS_FILE = os.getenv("DOCUMENT_DEFINITION_CONFIG", "example-conf.json")


class DocumentFieldDefinition:
    """
    Represents the definition of a document field.

    Attributes:
        field_name (str): The name of the field.
        required (bool): Indicates if the field is required. Default is False.
    """
    def __init__(self, field_name: str, required: bool = False):
        self.field_name = field_name
        self.required = required


class DocumentDefinitions:
    """
    Represents the definitions for a document.

    Attributes:
        saved_fields (dict[str, DocumentFieldDefinition]): A dictionary of saved fields.
        models (dict[str, str]): A dictionary of models.
        identifier (str): The identifier field.
        field_for_llm (str, optional): The field for LLM. Default is None.
    """
    def __init__(self, saved_fields: dict[str, DocumentFieldDefinition], models: dict[str, str],
                 identifier: str, field_for_llm: str = None):
        self.saved_fields = saved_fields
        self.models = models
        self.identifier = identifier
        self.field_for_llm = field_for_llm


def initialize_definitions():
    """
    Initializes the document definitions by reading the configuration file.

    Raises:
        ValueError: If the identifier field is not one of the saved fields or if any model field is not one of the saved fields.

    Returns:
        DocumentDefinitions: The initialized document definitions.
    """
    with open(DEFINITIONS_FILE, 'r', encoding='utf-8') as f:
        definitions = json.load(f)

        saved_fields = definitions['saved_fields']
        models = definitions['models']
        identifier_field = definitions['identifier_field']
        field_for_llm = definitions.get('field_for_llm', None)
        if identifier_field not in saved_fields.keys():
            raise ValueError("identifier_field must be one of the saved fields, check the configuration file")

        for embedded_field in models.values():
            if embedded_field not in saved_fields.keys():
                raise ValueError(f"{embedded_field} must be one of the saved fields {saved_fields.keys()}, check the configuration file")

        return DocumentDefinitions(saved_fields, models, identifier_field, field_for_llm)


definitions_singleton = None


def factory():
    """
    Factory method to get the singleton instance of DocumentDefinitions.

    Returns:
        DocumentDefinitions: The singleton instance of document definitions.
    """
    global definitions_singleton
    if definitions_singleton is None:
        definitions_singleton = initialize_definitions()
    return definitions_singleton


class Document:
    """
    Represents a document.

    Attributes:
        page_id (str): The ID of the page.
        fields (dict): The fields of the document.

    Raises:
        ValueError: If the fields do not match the required fields or if a required field is missing.
    """
    def __init__(self, page_id: str, fields: dict):
        definitions = factory()
        self.page_id = page_id
        if fields.keys() != definitions.saved_fields.keys():
            raise ValueError("fields do not match the required fields")
        for defined_field in definitions.saved_fields.values():
            if defined_field.required and defined_field.field_name not in fields:
                raise ValueError(f"field {defined_field.field_name} is required")
            if defined_field.field_name in fields:
                setattr(self, defined_field.field_name, fields[defined_field.field_name])
