from elasticsearch import Elasticsearch, helpers
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MERGED = BASE_DIR / "data" / "merged_companies.json"

if __name__ == "__main__":
    # Connect to Elasticsearch
    es = Elasticsearch("http://localhost:9200")
    try:
        print(es.info())
    except Exception as e:
        print("Connection error:", e)

    # Specify target index name
    index_name = "companies"

    # Create index with default settings if it doesn't exist
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)

    # Read and index each JSON line
    with open(MERGED, "r") as file:
        for line in file:
            doc = json.loads(line)
            es.index(index=index_name, document=doc)

    print("Data indexing completed successfully.")

