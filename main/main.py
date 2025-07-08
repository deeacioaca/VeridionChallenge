from fastapi import FastAPI
from elasticsearch import Elasticsearch

app = FastAPI()

es = Elasticsearch("http://elasticsearch:9200")  # Use service name as host in docker-compose network

@app.get("/")
def root():
    return {"message": "FastAPI with ElasticSearch is running"}

@app.get("/es_info")
def es_info():
    return es.info()
