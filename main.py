# main.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import Field
from typing import Optional, Any, Dict
from models import (
    UserCreatePayload,
    AddressCreatePayload,
    UsersWithAddressRequest,
    UsersWithAddressResponse,
    UserResponse,
    AddressListResponse,
    CompositeAddressCreate,
    CompositeAddressResponse,
    UserAddressesResponse,
    UserProfileResponse,
    AddressQuery,
)
from api_client import (
    get_addresses,
    delete_address,
    get_user,
    create_user,
    delete_user,
    create_address_atomic,
    get_address,
)
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI(title="Composite Microservice")

# In-memory mapping to demonstrate logical foreign-key relationships
# Maps address_id -> user_id
ADDR_USER_MAP = {}


@app.get("/addresses", response_model=AddressListResponse)
def addresses(
    limit: int = 10,
    offset: int = 0,
    name: Optional[str] = None,
    street: Optional[str] = None,
    unit: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: Optional[str] = None,
    as_geojson: bool = False,
):
    """List addresses with query parameters exposed in OpenAPI.
    """
    params = {
        "limit": limit,
        "offset": offset,
        "as_geojson": "true" if as_geojson else "false",
    }
    # optional filters
    if name:
        params["name"] = name
    if street:
        params["street"] = street
    if unit:
        params["unit"] = unit
    if city:
        params["city"] = city
    if state:
        params["state"] = state
    if postal_code:
        params["postal_code"] = postal_code
    if country:
        params["country"] = country

    return get_addresses(params)


@app.post("/addresses/query", response_model=AddressListResponse)
def addresses_query(query: AddressQuery):
    """Search addresses with a JSON body. Use this if you prefer JSON filters
    instead of URL query parameters.
    """
    params = query.model_dump()
    # Convert boolean to string the atomic addresses service expects
    if "as_geojson" in params:
        params["as_geojson"] = "true" if params["as_geojson"] else "false"
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    try:
        return get_addresses(params)
    except httpx.HTTPStatusError as e:
        # Upstream returned non-2xx
        status = e.response.status_code if e.response is not None else 502
        raise HTTPException(status_code=502, detail=f"Upstream addresses service error: {status} - {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/addresses/{address_id}")
def delete(address_id: str):
    # Forward delete to atomic addresses service and remove logical mapping
    result = delete_address(address_id)
    if address_id in ADDR_USER_MAP:
        del ADDR_USER_MAP[address_id]
    return result


# -----------------------------
# Delegation for Users (atomic user microservice)
# -----------------------------
@app.get("/users/{user_id}", response_model=UserResponse)
def users_get(user_id: int, request: Request):
    try:
        return get_user(user_id)
    except httpx.HTTPStatusError as e:
        # Map 404 from atomic service to a clear composite 404
        if e.response is not None and e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/users", response_model=UserResponse)
def users_create(payload: UserCreatePayload):
    # Pass-through to atomic users service using typed model so OpenAPI shows examples
    return create_user(payload.model_dump())


# -----------------------------
# Composite endpoints that combine users + addresses
# -----------------------------
@app.post("/addresses", response_model=CompositeAddressResponse)
def composite_create_address(payload: CompositeAddressCreate):
    """Composite create: enforce logical FK to users service before delegating.
    """
    user_id = payload.user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="`user_id` is required")

    # Verify user exists in users atomic microservice
    try:
        get_user(user_id)
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 404:
            raise HTTPException(status_code=400, detail=f"User {user_id} does not exist")
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Compose address payload for atomic service (remove user_id if atomic doesn't expect it)
    # Convert to dict and strip user_id for atomic address creation
    atomic_payload = {
        k: v for k, v in payload.model_dump().items() if k != "user_id"
    }

    created = create_address_atomic(atomic_payload)

    # Try to extract an id from created response to maintain mapping
    addr_id = None
    if isinstance(created, dict):
        addr_id = created.get("id") or created.get("data", {}).get("id")

    if addr_id:
        ADDR_USER_MAP[str(addr_id)] = int(user_id)

    # Return created resource augmented with logical link to user
    # Normalize created into AddressRead where possible
    return CompositeAddressResponse(address=created, user_id=user_id)


@app.get("/users/{user_id}/addresses", response_model=UserAddressesResponse)
def get_addresses_for_user(user_id: int):
    """Return all addresses associated with a user using the composite mapping.

    This demonstrates logical FK enforcement and uses threads to fetch each
    address from the atomic address service in parallel.
    """
    # Find address IDs belonging to user
    address_ids = [aid for aid, uid in ADDR_USER_MAP.items() if uid == int(user_id)]

    if not address_ids:
        return {"user_id": user_id, "addresses": []}

    results = []
    # Fetch addresses concurrently
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(get_address, aid): aid for aid in address_ids}
        for fut in as_completed(futures):
            aid = futures[fut]
            try:
                results.append(fut.result())
            except Exception:
                # If an address lookup fails, skip it (could happen if atomic resource removed)
                continue

    return UserAddressesResponse(user_id=user_id, addresses=results)


@app.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def user_profile(user_id: int):
    """Composite view that returns user info and their addresses.

    This endpoint fetches the user and addresses in parallel (threads) to
    demonstrate concurrent delegation.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        future_user = ex.submit(get_user, user_id)
        future_addresses = ex.submit(lambda: get_addresses_for_user(user_id))
        # wait for both
        try:
            results["user"] = future_user.result()
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"User lookup failed: {e}")
        try:
            results["addresses"] = future_addresses.result().get("addresses", [])
        except Exception:
            results["addresses"] = []

    return UserProfileResponse(user=results["user"], addresses=results["addresses"])


@app.post("/users_with_address", response_model=UsersWithAddressResponse)
def create_user_and_address(payload: UsersWithAddressRequest) -> UsersWithAddressResponse:
    """Create a user and an address in a single composite operation.

    Payload shape:
    {
      "user": { ... user fields ... },
      "address": { ... address fields ... }
    }

    The composite will:
    - create the user in the atomic users service
    - on success, create the address in the atomic addresses service
    - store the logical mapping address_id -> user_id
    - on address creation failure, attempt to rollback (delete) the newly-created user
    """
    user_payload = payload.user.model_dump()
    address_payload = payload.address.model_dump()
    if not user_payload or not address_payload:
        raise HTTPException(status_code=400, detail="`user` and `address` objects are required")

    # 1) Create user
    try:
        created_user = create_user(user_payload)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Upstream user creation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Try to extract user id (supports 'user_id' or 'id')
    user_id = None
    if isinstance(created_user, dict):
        user_id = created_user.get("user_id") or created_user.get("id")

    if user_id is None:
        # If we can't determine a user id, treat as failure
        raise HTTPException(status_code=502, detail="User created but no id returned from users service")

    # 2) Create address (attach user_id to address for composite-level FK)
    try:
        # Add user_id to address payload for the composite mapping (composite strips before calling atomic)
        address_payload_with_user = {**address_payload, "user_id": user_id}
        created_address = create_address_atomic(address_payload_with_user)
    except httpx.HTTPStatusError as e:
        # Address creation failed — attempt to rollback user
        try:
            delete_user(user_id)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"Upstream address creation failed: {e}")
    except Exception as e:
        try:
            delete_user(user_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

    # 3) Record mapping if we can extract address id
    addr_id = None
    if isinstance(created_address, dict):
        addr_id = created_address.get("id") or created_address.get("data", {}).get("id")

    if addr_id:
        ADDR_USER_MAP[str(addr_id)] = int(user_id)

    return UsersWithAddressResponse(user=created_user, address=created_address)
