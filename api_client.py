# api_clients.py
import os
import httpx

# Configure atomic service base URLs via environment variables for flexibility.
USERS_BASE = os.getenv("USERS_BASE", "http://localhost:8000/api/v1/users")
ADDRESSES_BASE = os.getenv("ADDRESSES_BASE", "http://localhost:8001/addresses")


def _url(base: str, *parts: object) -> str:
	"""Join base and parts into a single URL, avoiding duplicate slashes.
	"""
	url = base.rstrip('/')
	for p in parts:
		url += '/' + str(p).lstrip('/')
	return url


def get_addresses(params=None):
	"""Fetch addresses from the atomic addresses microservice.

	Try both trailing and non-trailing base URL forms to avoid 307 redirect errors
	when upstream differs on slash handling.
	"""
	exc = None
	for candidate in (_url(ADDRESSES_BASE), _url(ADDRESSES_BASE, "")):
		try:
			r = httpx.get(candidate, params=params, timeout=10)
			r.raise_for_status()
			return r.json()
		except httpx.HTTPStatusError as e:
			exc = e
			# try next candidate
			continue
	if exc:
		raise exc
	raise RuntimeError("Address list fetch failed for unknown reasons")


def get_address(address_id: str):
	r = httpx.get(_url(ADDRESSES_BASE, address_id), timeout=10)
	r.raise_for_status()
	return r.json()


def create_address_atomic(address_payload: dict):
	"""Create an address in the atomic addresses microservice.
	"""
	# Some atomic services differ on trailing-slash handling; try both forms.
	exc = None
	for candidate in (_url(ADDRESSES_BASE), _url(ADDRESSES_BASE, "")):
		try:
			r = httpx.post(candidate, json=address_payload, timeout=10)
			r.raise_for_status()
			return r.json()
		except httpx.HTTPStatusError as e:
			exc = e
			# if redirect, attempt next candidate
			continue
	# If we get here, all attempts failed
	if exc:
		raise exc
	raise RuntimeError("Address creation failed for unknown reasons")


def delete_address(address_id: str):
	"""Delegate delete call to atomic addresses microservice"""
	r = httpx.delete(_url(ADDRESSES_BASE, address_id), timeout=10)
	r.raise_for_status()
	# Some atomic services return 204 No Content; normalize to dict
	if r.status_code == 204 or not r.text:
		return {"status": "deleted", "id": address_id}
	return r.json()


def get_user(user_id: int):
	r = httpx.get(_url(USERS_BASE, user_id), timeout=10)
	r.raise_for_status()
	try:
		return r.json()
	except Exception:
		# Upstream may return Python-style reprs (e.g. None) instead of valid JSON.
		# Try a tolerant fallback by replacing Python `None`/`True`/`False` with
		# JSON `null`/`true`/`false` and parsing.
		import json
		text = r.text
		cleaned = text.replace("None", "null").replace("True", "true").replace("False", "false")
		return json.loads(cleaned)


def create_user(user_payload: dict):
	r = httpx.post(_url(USERS_BASE, ""), json=user_payload, timeout=10)
	r.raise_for_status()
	try:
		return r.json()
	except Exception:
		import json
		text = r.text
		cleaned = text.replace("None", "null").replace("True", "true").replace("False", "false")
		return json.loads(cleaned)


def delete_user(user_id: int):
	"""Delete a user in the atomic users microservice."""
	r = httpx.delete(_url(USERS_BASE, user_id), timeout=10)
	# raise for status to allow caller to catch errors consistently
	r.raise_for_status()
	if r.status_code == 204 or not r.text:
		return {"status": "deleted", "id": user_id}
	return r.json()