# Profile system

The Profile system performs basic CRUD operations on the profile, and relies on FastAPI.

## Paths / endpoints
`/profile/profile`
- `GET`: Fetch all profile information as JSON
- `PUT`: Update all profile information as JSON (in request body)

`/profile/preferences`
- `GET`: Fetch dietary preferences for a specific user as JSON
- `PUT`: Update dietary preferences for a specific user

`/profile/restrictions`
- `GET`: Fetch dietary restrictions for a specific user as JSON
- `PUT`: Update dietary restrictions for a specific user

`/profile/ingredients`
- `GET`: Fetch available ingredients for a specific user as JSON
- `PUT`: Update available ingredients for a specific user

`/profile/tools`
- `GET`: Fetch available tools for a specific user as JSON
- `PUT`: Update available tools for a specific user

`/profile/location`
- `GET`: Fetch current location for a specific user returned as JSON `{id, latitude ,longitude}`
- `PUT`: Update location using id, and optionally latitude and longitude. Updates both Profile and Location tables.

`/profile/new`
- `POST`: Initiate a new empty profile for a new user

## Dependencies
- FastAPI ([homepage](https://fastapi.tiangolo.com/)): `pip install "fastapi[standard]"`
- Supabase ([docs](https://supabase.com/docs/reference/python/introduction)): `pip install supabase`
- Dotenv ([PyPi](https://pypi.org/project/python-dotenv/)): `pip install python-dotenv`
