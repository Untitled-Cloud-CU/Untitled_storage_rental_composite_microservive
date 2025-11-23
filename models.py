from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

from typing import List
from datetime import datetime



class UserCreatePayload(BaseModel):
    first_name: str = Field(..., example="Amy")
    last_name: str = Field(..., example="Adams")
    email: str = Field(..., example="amy.adams@example.com")
    password: str = Field(..., example="Passw0rd1")
    phone: Optional[str] = Field(None, example="555-0100")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "Amy",
                    "last_name": "Adams",
                    "email": "amy.adams@example.com",
                    "password": "Passw0rd1",
                    "phone": "555-0100"
                }
            ]
        }
    }


class AddressCreatePayload(BaseModel):
    name: str = Field(..., example="Amy Home")
    street: str = Field(..., example="123 Main St")
    unit: Optional[str] = Field(None, example="Apt 4B")
    city: str = Field(..., example="Seattle")
    state: Optional[str] = Field(None, example="WA")
    postal_code: Optional[str] = Field(None, example="98101")
    country: str = Field(..., example="USA")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Amy Home",
                    "street": "123 Main St",
                    "unit": "Apt 4B",
                    "city": "Seattle",
                    "state": "WA",
                    "postal_code": "98101",
                    "country": "USA"
                }
            ]
        }
    }


class UsersWithAddressRequest(BaseModel):
    user: UserCreatePayload
    address: AddressCreatePayload

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": UserCreatePayload.model_json_schema()["examples"][0],
                    "address": AddressCreatePayload.model_json_schema()["examples"][0]
                }
            ]
        }
    }


class UsersWithAddressResponse(BaseModel):
    user: Dict[str, Any] = Field(...)
    address: Dict[str, Any] = Field(...)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": {"user_id": 1, "first_name": "Amy", "last_name": "Adams", "email": "amy.adams@example.com"},
                    "address": {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "Amy Home", "street": "123 Main St", "city": "Seattle", "country": "USA"}
                }
            ]
        }
    }


class UserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    _links: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "first_name": "John",
                    "last_name": "Smith",
                    "email": "john.smith@email.com",
                    "phone": "555-0101",
                    "address": "123 Main St",
                    "city": "Seattle",
                    "state": "WA",
                    "zip_code": "98101",
                    "status": "active"
                }
            ]
        }
    }


class AddressRead(BaseModel):
    id: str
    name: Optional[str] = None
    street: Optional[str] = None
    unit: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    links: Optional[List[Dict[str, Any]]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Amy Home",
                    "street": "123 Main St",
                    "city": "Seattle",
                    "state": "WA",
                    "postal_code": "98101",
                    "country": "USA",
                    "links": [{"rel": "self", "href": "/addresses/550e8400-e29b-41d4-a716-446655440000"}]
                }
            ]
        }
    }


class AddressListResponse(BaseModel):
    data: List[AddressRead]
    links: List[Dict[str, Any]]
    total: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": [AddressRead.model_json_schema()["examples"][0]],
                    "links": [{"rel": "current", "href": "/addresses?limit=10&offset=0"}],
                    "total": 1
                }
            ]
        }
    }


class CompositeAddressCreate(BaseModel):
    user_id: int
    name: str
    street: str
    unit: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "name": "Amy Home",
                    "street": "123 Main St",
                    "city": "Seattle",
                    "country": "USA"
                }
            ]
        }
    }


class AddressQuery(BaseModel):
    limit: Optional[int] = Field(10, example=10)
    offset: Optional[int] = Field(0, example=0)
    name: Optional[str] = Field(None, example="Amy Home")
    street: Optional[str] = Field(None, example="123 Main St")
    unit: Optional[str] = Field(None, example="Apt 4B")
    city: Optional[str] = Field(None, example="Seattle")
    state: Optional[str] = Field(None, example="WA")
    postal_code: Optional[str] = Field(None, example="98101")
    country: Optional[str] = Field(None, example="USA")
    as_geojson: Optional[bool] = Field(False, example=False)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "limit": 10,
                    "offset": 0,
                    "city": "Seattle",
                    "as_geojson": False
                }
            ]
        }
    }


class CompositeAddressResponse(BaseModel):
    address: AddressRead
    user_id: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "address": AddressRead.model_json_schema()["examples"][0],
                    "user_id": 1
                }
            ]
        }
    }


class UserAddressesResponse(BaseModel):
    user_id: int
    addresses: List[AddressRead]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 1,
                    "addresses": [AddressRead.model_json_schema()["examples"][0]]
                }
            ]
        }
    }


class UserProfileResponse(BaseModel):
    user: UserResponse
    addresses: List[AddressRead]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": UserResponse.model_json_schema()["examples"][0],
                    "addresses": [AddressRead.model_json_schema()["examples"][0]]
                }
            ]
        }
    }
