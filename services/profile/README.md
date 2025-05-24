# Profile & Auth Service

This service manages authentication and user profiles, and acts as middleware between the frontend and other backend services. Due to personal experience and preference, this service is written in Rust and has no runtime dependencies other than an active internet connection. To build, it requires only Cargo and the Rust toolchain (nightly) (see: [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install)) and an internet connection.

### Request Information

#### General Requests

Other than login and signup requests, all requests should contain the following:<br>

| Header | DataType |
|--|--|
| `X-User-Uid`| `String` |
| `Acces-Token`| `String` |
| `Refresh-Token`| `String` |

And should then have the request formatted according to their target service in the body.

The Auth service will validate these details before passing the request to the intended service, which will be identified by matching the request path.

| Path | Action |
|------|--------|
|`/auth/login` | Login |
|`/auth/signup` | Sign up |
|`/profile/*` | Transfer request to profile service |
|`/recipe/*` | Transfer request to recipe service |
|`/ets/*` | Transfer request to 'eat together' service |
|`/menu/*` | Transfer request to menu service |

#### Sign up

- Request type: `POST`
- Path: `/auth/signup`
- Body: JSON
  ```
  Body: {
    "email": "user@domain.com",
    "password": "encrypted-password",
    "password2": "encrypted-password"
  }
  ```
- Response if STATUS=SUCCESS:
  - Body: JSON
    ```
    Body: {
      "X-User-Uid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "Access-Token": "LongToken",
      "Refresh-Token": "ShortToken",
    }
    ```


#### Login

- Request type: `GET`
- Path: `/auth/login`
- Body: JSON
  ```
  Body: {
    "email": "user@domain.com",
    "password": "encrypted-password",
  }
  ``` 
- Response if STATUS=SUCCESS:
  - Body: JSON
    ```
    Body: {
      "X-User-Uid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "Access-Token": "LongToken",
      "Refresh-Token": "ShortToken",
    }
    ```

