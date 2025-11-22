# api_clients.py
import httpx

ATOMIC_A_BASE = "https://atomic-a.example.com"
ATOMIC_B_BASE = "https://atomic-b.example.com"

def get_addresses(params=None):
    """Fetch addresses from atomic microservice A"""
    r = httpx.get(f"{ATOMIC_A_BASE}/addresses", params=params)
    r.raise_for_status()
    return r.json()

def delete_address(address_id: str):
    """Delegate delete call to atomic microservice"""
    r = httpx.delete(f"{ATOMIC_A_BASE}/addresses/{address_id}")
    r.raise_for_status()
    return r.json()