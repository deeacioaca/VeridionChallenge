from fastapi import FastAPI
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from typing import Optional
import uvicorn

app = FastAPI()

# Elasticsearch connection
es = Elasticsearch("http://localhost:9200")
index_name = "companies"


# Input schema
class CompanyInput(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    facebook: Optional[str] = None


@app.post("/match_company")
def match_company(data: CompanyInput):
    query = {
        "size": 1,
        "query": {
            "bool": {
                "should": [],
                "minimum_should_match": 1
            }
        }
    }

    # Weighted fuzzy match on name
    if data.name:
        query["query"]["bool"]["should"].append({
            "match": {
                "company_commercial_name": {
                    "query": data.name,
                    "fuzziness": "AUTO",
                    "boost": 3
                }
            }
        })
        query["query"]["bool"]["should"].append({
            "match": {
                "company_all_available_names": {
                    "query": data.name,
                    "fuzziness": "AUTO",
                    "boost": 3
                }
            }
        })

    # Match on website
    if data.website:
        query["query"]["bool"]["should"].append({
            "match": {
                "domain": {
                    "query": data.website.replace("https://", "").replace("http://", "").replace("www.", ""),
                    "boost": 4
                }
            }
        })

    # Match on phone number
    if data.phone:
        query["query"]["bool"]["should"].append({
            "match": {
                "phone_numbers": {
                    "query": data.phone.replace("(", "").replace(")", "").replace("-", "").replace(" ", ""),
                    "boost": 5
                }
            }
        })

    # Match on facebook in social_links
    if data.facebook:
        query["query"]["bool"]["should"].append({
            "match": {
                "social_links": {
                    "query": data.facebook,
                    "boost": 2
                }
            }
        })

    # Search in Elasticsearch
    res = es.search(index=index_name, body=query)

    # Return the best matching company or no match found
    if res["hits"]["hits"]:
        return {"match_found": True, "company_profile": res["hits"]["hits"][0]["_source"]}
    else:
        return {"match_found": False, "company_profile": None}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
