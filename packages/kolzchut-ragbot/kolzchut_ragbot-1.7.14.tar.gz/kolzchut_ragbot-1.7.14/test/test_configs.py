bad_conf_1 = '''
{
  "identifier_field": "no_such_field",
  "saved_fields": {
    "title": "text",
    "doc_id": "integer",
    "content": "text"
  },
  "models": {
    "me5_large-v10": "content"
  }
}
'''

bad_conf_2 = '''
{
  "identifier_field": "doc_id",
    "saved_fields": {
    "title": "text",
    "doc_id": "integer",
    "content": "text"
  },
  "models": {
    "me5_large-v10": "content",
    "OMG": "no_such_field"
  }
}
'''

good_conf = '''
{
  "identifier_field": "doc_id",
    "saved_fields": {
    "title": "text",
    "doc_id": "integer",
    "content": "text"
  },
  "models": {
    "me5_large-v10": "content"
  }
}
'''