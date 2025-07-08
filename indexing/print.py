from elasticsearch import Elasticsearch

if __name__ == "__main__":

    es = Elasticsearch("http://localhost:9200")

    # Retrieve and print first 5 documents from the 'companies' index
    res = es.search(index="companies", query={"match_all": {}})

    for doc in res["hits"]["hits"]:
        print(doc["_source"])