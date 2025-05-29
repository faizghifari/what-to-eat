# Auth service

The Auth service serves as What To Eat (W2E)'s middleware. That is to say, it is the only service open to external access, and all communication from or to the W2E client/UI goes through this service.

The service is therefore divided into two functionally distinct components:

- Router: handles incoming/outgoing connections, and forwards HTTP requests to their expected destination.
- Auth: handles authentication, that is (e.g. login, signup, etc...), and verifies that incoming requests are from valid users.

## Building

This service is written in Rust, and building it requires Cargo. We recommend using Rustup to install Rust with the nightly toolchain (see: [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install)).

For faster development build times, we recommend installing the "Cranelift" backend:
```
  > rustup component add rustc-codegen-cranelift
```
Additionally, the [mold](https://github.com/rui314/mold) linker can improve build times on Linux. It can be activated by adding `"-C,"link-arg=-fuse-ld=mold",` to `rustflags` in `.cargo/config.toml`.

To build the service, simply run `cargo b` (`cargo build`) for development (unoptimised, debug messages), or `cargo br` (`cargo build --release`) for release (more optimised, not debug messages).

### Dependencies
- clang
- pkg-config
- openssl

## Running
If you built the service using Cargo, you can either use Cargo to run it:
```
cargo r
cargo run
cargo rr
cargo run --release
```
Or you can access the built executable at `./target/[release|debug]/auth[.exe]`.

If you downloaded a prebuilt executable, you can just run it.

### Environment Variables
Please note that the following environment variables must be set (and valid) to successfully run the service:
- `SUPABASE_URL`
- `SUPABASE_API_KEY`
- `SUPABASE_JWT_SECRET`

## Documentation
Any requests should be sent to this service, and it therefore accepts a variety of paths, methods, and request contents. However, there are some required contents and known responses, which will be outlined here.

### Router API
**General Request:**
- Headers: `X-User-Uid`:`String(Uuid)`
- Query Parameters: `Access-Token`:`TokenStr`

**Responses**

Status Code: `400` (BAD_REQUEST)
- Meaning: Path or method are invalid

Status Code: `401` (UNAUTHORIZED)
- Meaning: Invalid credentials

Status Code: `500` (INTERNAL_SERVER_ERROR)
- Meaning: Something went wrong on the server side, mabybe try again later

### Auth API
#### Sign up

Request to sign up a new user (logs in existing users):

**Request**:
- Method: `POST`
- Path: `/auth/signup`
- Body:
  ```
  JSON {
    email:String,
    password_1:String,
    password_2:String
  }
  ```

**Responses**:
Status Code: `200` (OK)
- Meaning: Successfully signed up and logged in
- Body:
  ```
  JSON{
    x_user_uuid: String | Uuid,
    access_token: String,
    refresh_token: String,
  }
  ```

Status Code: `400` (BAD_REQUEST)
- Meaning: Failed
- Reason: Could not read necessary information from request body

Status Code: `401` (UNAUTHORIZED)
- Meaning: Failed
- Reason: Invalid credentials (email or password incorrect)

Status Code: `409` (CONFLICT)
- Meaning: Failed
- Reason: Submitted passwords do not match

Status Code: `500` (INTERNAL_SERVER_ERROR)
- Meaning: Failed
- Reason: Something went wrong on the server side, mabybe try again later.

#### Log in

Request to log existing user in:

**Request**:
- Method: `POST`
- Path: `/auth/login`
- Body:
  ```
  JSON {
    email: String,
    password: String,
  }
  ```

**Responses**:
Status Code: `200` (OK)
- Meaning: Successfully logged in
- Body:
  ```
  JSON{
    x_user_uuid: String | Uuid,
    access_token: String,
    refresh_token: String,
  }
  ```

Status Code: `400` (BAD_REQUEST)
- Meaning: Failed
- Reason: Could not read necessary information from request body

Status Code: `401` (UNAUTHORIZED)
- Meaning: Failed
- Reason: Invalid credentials (email or password incorrect, or user not signed up)

Status Code: `500` (INTERNAL_SERVER_ERROR)
- Meaning: Failed
- Reason: Something went wrong on the server side, mabybe try again later.


#### Log out

Request to sign up a new user (logs in existing users):

**Request**:
- Method: `POST`
- Path: `/auth/logout`
- Query Parameters: `Access-Token=[TokenStr]`

**Responses**:
Status Code: `200` (OK)
- Meaning: Successfully signed up and logged in
- Body:
  ```
  JSON{
    x_user_uuid: String | Uuid,
    access_token: String,
    refresh_token: String,
  }
  ```

Status Code: `400` (BAD_REQUEST)
- Meaning: Failed
- Reason: Could not read necessary information from request parameters

Status Code: `500` (INTERNAL_SERVER_ERROR)
- Meaning: Failed
- Reason: Something went wrong on the server side, mabybe try again later.

## TODO
- [ ] Make service run in Docker
- [ ] Add service URLs and PORTs to environment variables
- [ ] Extensive testing
