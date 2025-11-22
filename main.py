# main.py
from fastapi import FastAPI
from api_client import get_addresses, delete_address

app = FastAPI(title="Composite Microservice")

@app.get("/addresses")
def addresses(params: dict = None):
    return get_addresses(params)

@app.delete("/addresses/{address_id}")
def delete(address_id: str):
    return delete_address(address_id)
