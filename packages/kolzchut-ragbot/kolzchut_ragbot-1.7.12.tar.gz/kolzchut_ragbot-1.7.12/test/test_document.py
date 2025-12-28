import pytest
from unittest.mock import patch, mock_open
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kolzchut_ragbot.Document import initialize_definitions


class TestDocument:

    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "saved_fields": {"doc_id": "doc_id"},
        "models": {"model1": "doc_id"},
        "identifier_field": "doc_id"
    }))
    @patch('os.getenv', return_value='example-conf.json')
    def test_initialize_definitions_good(self, mock_getenv, mock_open):
        definitions = initialize_definitions()
        assert definitions.saved_fields == {"doc_id": "doc_id"}
        assert definitions.models == {"model1": "doc_id"}
        assert definitions.identifier == "doc_id"

    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "saved_fields": {"field1": {"field_name": "field1", "required": True}},
        "models": {"model1": "field1"},
        "identifier_field": "no_such_field"
    }))
    @patch('os.getenv', return_value='example-conf.json')
    def test_initialize_definitions_bad_identifier(self, mock_getenv, mock_open):
        with pytest.raises(ValueError) as excinfo:
            initialize_definitions()
        assert "identifier_field must be one of the saved fields" in str(excinfo.value)

    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "saved_fields": {"field1": {"field_name": "field1", "required": True}},
        "models": "no_such_field",
        "identifier_field": "doc_id"
    }))
    @patch('os.getenv', return_value='example-conf.json')
    def test_initialize_definitions_bad_model(self, mock_getenv, mock_open):
        with pytest.raises(ValueError) as excinfo:
            initialize_definitions()
        assert "must be one of the saved fields" in str(excinfo.value)
