# kolzchut-ragbot

## Overview

This project is a search engine that uses machine learning models and Elasticsearch to provide advanced document retrieval.
You can use [kolzchut-ragbot](https://github.com/shmuelrob/rag-bot) to demonstrate the engine's document retrieval abilities.

## Features

- Document representation and validation
- Document embedding and indexing in Elasticsearch
- Advanced search using machine learning model
- Integration with LLM (Large Language Model) client for query answering

## Installation

### From PyPI

```bash
pip install kolzchut-ragbot
```

### From Source

1. Clone the repository:
   
   ```bash
   git clone https://github.com/shmuelrob/rag-bot.git
   cd rag-bot
   ```

2. Create a virtual environment and activate it:  

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the required dependencies:  

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set the following environment variables:

- `ES_EMBEDDING_INDEX`: The name of the Elasticsearch index for embeddings.
- `TOKENIZER_LOCATION`: The location of the tokenizer model.
