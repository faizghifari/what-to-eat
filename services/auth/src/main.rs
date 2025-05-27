use interprocess::local_socket::tokio::Stream as LocalStream;
use poem::{
    Body, IntoResponse, Request, Route, Server, get, handler, http::StatusCode,
    listener::TcpListener, post,
};
use subservices::auth::UserTokens;
use tokio::io::AsyncReadExt;

mod subservices;

fn main() {
    use tokio::runtime::Runtime;

    // Initialise logger with relevant level
    #[cfg(debug_assertions)]
    simple_logger::init_with_level(log::Level::Debug).unwrap();
    #[cfg(not(debug_assertions))]
    simple_logger::init_with_level(log::Level::Info).unwrap();

    // Create Tokio runtime
    if let Ok(runtime) = Runtime::new() {
        log::debug!("[ROUTER] Created tokio runtime successfully!");
        // Run concurrent and parallel systems
        runtime.block_on(run_combined_system())
    } else {
        log::error!("[ROUTER] Failed to create Tokio runtime!");
    }
}

// Launch the various concurrent middleware services in parallel
async fn run_combined_system() {
    use tokio::task::JoinHandle;

    let auth_handle: JoinHandle<_> = tokio::spawn(async move { subservices::auth::run().await });
    let profile_handle: JoinHandle<_> =
        tokio::spawn(async move { subservices::profile::run().await });
    let server_handle: JoinHandle<_> = tokio::spawn(async move { create_http_server().await });

    let results = tokio::try_join!(auth_handle, profile_handle, server_handle);
    if let Err(e) = results {
        log::error!("[ROUTER] Failed to start parallel auth, profile and router services: {e}");
    }
}

// Routing service
async fn create_http_server() -> Result<(), std::io::Error> {
    log::debug!("[ROUTER] Starting HTTP server...");
    let app: Route = create_router();
    Server::new(TcpListener::bind((std::net::Ipv6Addr::LOCALHOST, 5000)))
        .run(app)
        .await
}

fn create_router() -> Route {
    Route::new()
        .at("/auth/login", get(auth_login))
        .at("/auth/signup", post(auth_signup))
        .at("/profile/*", get(auth_forward_to_profile))
        .at("/recipe/*", get(auth_forward_to_recipe))
        .at("/ets/*", get(auth_forward_to_ets))
        .at("/menu/*", get(auth_forward_to_menu))
}

struct LoginResponse {
    err: Option<poem::Error>,
    data: Option<subservices::auth::SignupOrLoginResponse>,
}
impl LoginResponse {
    fn from_err(err: poem::Error) -> Self {
        Self {
            err: Some(err),
            data: None,
        }
    }
}
impl IntoResponse for LoginResponse {
    fn into_response(self) -> poem::Response {
        let response: poem::ResponseBuilder = poem::Response::builder();
        if self.data.is_none() {
            return response.status(self.err.unwrap().status()).finish();
        }
        let data: subservices::auth::SignupOrLoginResponse = self.data.unwrap();
        let status_code: StatusCode;
        if data.x_user_uid.is_empty() {
            status_code = StatusCode::NOT_ACCEPTABLE
        } else {
            match self.err {
                None => status_code = StatusCode::OK,
                Some(err) => return err.into_response(),
            }
        };

        if !status_code.is_success() {
            return response.status(status_code).finish();
        }
        if let Ok(body) = serde_json::to_string(&data) {
            response.body(body)
        } else {
            response.status(StatusCode::UNPROCESSABLE_ENTITY).finish()
        }
    }
}

#[handler]
async fn auth_signup(body: Body) -> LoginResponse {
    log::debug!("[ROUTER:SIGNUP] Signup request received. Rerouting!");

    if let Ok(signup_info) = body.into_json::<subservices::auth::SignupInfo>().await {
        log::debug!("[ROUTER:SIGNUP] Grabbed request body.");

        let mut message: Vec<u8> = vec![1];
        message.extend_from_slice(&serde_cbor::to_vec(&signup_info).unwrap_or_else(|_| {
            log::error!("Failed to reserialise signup info.");
            vec![]
        }));
        message.push(u8::MAX);

        let stream: Result<LocalStream, _> = subservices::auth::create_auth_stream().await;
        if let Err(ref e) = stream {
            log::error!("[ROUTER:SIGNUP] Failed to connect to Auth service: {e}");
            LoginResponse::from_err(poem::Error::from_string(
                "Router failed to connect to Auth service",
                poem::http::StatusCode::SERVICE_UNAVAILABLE,
            ));
        }
        let stream: LocalStream = stream.unwrap();

        match subservices::auth::send_to_auth(&stream, &message).await {
            Err(e) => {
                log::error!("[ROUTER:SIGNUP] Failed to send Signup request to Auth service: {e}");
                LoginResponse::from_err(poem::Error::from_string(
                    "Router failed to send signup request to Auth service",
                    poem::http::StatusCode::SERVICE_UNAVAILABLE,
                ))
            }
            Ok(mut stream) => {
                let mut response_buffer: Vec<u8> = Vec::with_capacity(512);
                if let Err(e) = stream.read_to_end(&mut response_buffer).await {
                    log::error!("[ROUTER:SIGNUP] Failed to read signup response: {e}");
                }
                if let Ok(response) = serde_cbor::from_slice::<
                    subservices::auth::SignupOrLoginResponse,
                >(&response_buffer)
                {
                    log::debug!("[ROUTER:SIGNUP] Received response from signup: {response:#?}");
                    LoginResponse {
                        err: None,
                        data: Some(response),
                    }
                } else {
                    log::error!("[ROUTER:SIGNUP] Failed to deserialise signup response");
                    LoginResponse::from_err(poem::Error::from_string(
                        "Failed to deserialise signup response: {e}",
                        StatusCode::UNPROCESSABLE_ENTITY,
                    ))
                }
            }
        }
    } else {
        log::error!("[ROUTER:SIGNUP] Failed to deserialise Signup request contents!");
        LoginResponse::from_err(poem::Error::from_string(
            "Failed to deserialise signup request.",
            StatusCode::UNPROCESSABLE_ENTITY,
        ))
    }
}

#[handler]
async fn auth_login(body: Body) -> LoginResponse {
    log::debug!("[ROUTER:LOGIN] Signup request received. Rerouting!");

    if let Ok(login_info) = body.into_json::<subservices::auth::LoginInfo>().await {
        log::debug!("[ROUTER:LOGIN] Grabbed request body: {login_info:#?}");

        let mut message: Vec<u8> = vec![2];
        message.extend_from_slice(&serde_cbor::to_vec(&login_info).unwrap_or_else(|_| {
            log::error!("Failed to reserialise signup info.");
            vec![]
        }));
        message.push(u8::MAX);

        let stream: Result<LocalStream, _> = subservices::auth::create_auth_stream().await;
        if let Err(e) = stream {
            log::error!("[ROUTER:LOGIN] Failed to connect to Auth service: {e}");
            return LoginResponse::from_err(poem::Error::from_string(
                format!("Router failed to connect to Auth service: {e}"),
                poem::http::StatusCode::SERVICE_UNAVAILABLE,
            ));
        }
        let stream: LocalStream = stream.unwrap();

        match subservices::auth::send_to_auth(&stream, &message).await {
            Err(e) => {
                log::error!("[ROUTER:LOGIN] Failed to send Login request to Auth service: {e}");
                LoginResponse::from_err(poem::Error::from_string(
                    format!("Router failed to send login request to Auth service: {e}"),
                    poem::http::StatusCode::SERVICE_UNAVAILABLE,
                ))
            }
            Ok(mut stream) => {
                let mut response_buffer: Vec<u8> = Vec::with_capacity(512);
                if let Err(e) = stream.read_to_end(&mut response_buffer).await {
                    log::error!("[ROUTER:LOGIN] Failed to read login response: {e}");
                    return LoginResponse::from_err(poem::Error::from_string(
                        format!("Failed to read login response: {e}"),
                        StatusCode::UNPROCESSABLE_ENTITY,
                    ));
                }
                if let Ok(response) = serde_cbor::from_slice::<
                    subservices::auth::SignupOrLoginResponse,
                >(&response_buffer)
                {
                    log::debug!("[ROUTER:LOGIN] Received response from login: {response:#?}");
                    LoginResponse {
                        err: None,
                        data: Some(response),
                    }
                } else {
                    log::error!("[ROUTER:LOGIN] Failed to deserialise login response");
                    LoginResponse::from_err(poem::Error::from_string(
                        "Failed to deserialise login response.",
                        StatusCode::UNPROCESSABLE_ENTITY,
                    ))
                }
            }
        }
    } else {
        log::error!("[ROUTER:LOGIN] Failed to deserialise login request contents!");
        LoginResponse::from_err(poem::Error::from_string(
            "Failed to read signup request",
            StatusCode::UNPROCESSABLE_ENTITY,
        ))
    }
}

async fn pass_through_auth(request: &Request) -> Result<bool, poem::Error> {
    let x_user_uid: String = request
        .header("X-User-Uid")
        .ok_or_else(|| {
            log::error!("[ROUTER:AUTHCHECK] Failed to retrieve uuid from header");
            poem::Error::from_string("Failed find header 'X-User-Uid'", StatusCode::BAD_REQUEST)
        })?
        .to_string();
    let access_token: String = request
        .header("Access-Token")
        .ok_or_else(|| {
            log::error!("[ROUTER:AUTHCHECK] Failed to retrieve access token from header");
            poem::Error::from_string("Failed find header 'Access-Token'", StatusCode::BAD_REQUEST)
        })?
        .to_string();
    let refresh_token: String = request
        .header("Refresh-Token")
        .ok_or_else(|| {
            log::error!("[ROUTER:AUTHCHECK] Failed to retrieve refresh token from header");
            poem::Error::from_string(
                "Failed find header 'Refresh-Token'",
                StatusCode::BAD_REQUEST,
            )
        })?
        .to_string();

    let user_tokens: UserTokens = UserTokens {
        x_user_uid,
        access_token,
        refresh_token,
    };

    let mut message: Vec<u8> = vec![4];
    message.extend_from_slice(&serde_cbor::to_vec(&user_tokens).unwrap_or_else(|_| {
        log::error!("[ROUTER:AUTHCHECK] Failed to reserialise tokens.");
        vec![]
    }));
    message.push(u8::MAX);

    let stream: Result<LocalStream, _> = subservices::auth::create_auth_stream().await;
    if let Err(e) = stream {
        log::error!("[ROUTER:AUTHCHECK] Failed to connect to Auth service: {e}");
        return Err(poem::Error::from_string(
            "Router failed to connect to Auth service",
            poem::http::StatusCode::SERVICE_UNAVAILABLE,
        ));
    }
    let stream: LocalStream = stream.unwrap();

    match subservices::auth::send_to_auth(&stream, &message).await {
        Err(e) => {
            log::error!("[ROUTER:AUTHCHECK] Failed to send Login request to Auth service: {e}");
            Err(poem::Error::from_string(
                "Router failed to send login request to Auth service",
                poem::http::StatusCode::SERVICE_UNAVAILABLE,
            ))
        }
        Ok(mut stream) => {
            let mut response_buffer: Vec<u8> = Vec::with_capacity(8);
            if let Err(e) = stream.read_to_end(&mut response_buffer).await {
                log::error!("[ROUTER:AUTHCHECK] Failed to read login response: {e}");
                return Err(poem::Error::from_string(
                    format!("Failed to read login response: {e}"),
                    StatusCode::UNPROCESSABLE_ENTITY,
                ));
            }
            if let Ok(response) = serde_cbor::from_slice::<Result<bool, String>>(&response_buffer) {
                match response {
                    Ok(response) => Ok(response),
                    Err(msg) => Err(poem::Error::from_string(
                        msg,
                        StatusCode::INTERNAL_SERVER_ERROR,
                    )),
                }
            } else {
                Err(poem::Error::from_string(
                    "Failed to deserialise auth response.",
                    StatusCode::INTERNAL_SERVER_ERROR,
                ))
            }
        }
    }
}

#[handler]
async fn auth_forward_to_profile(request: &Request, _body: Body) -> Result<(), poem::Error> {
    log::debug!("[ROUTER:PROFILE] Profile service called!");
    let is_authenticated: Result<bool, _> = pass_through_auth(request).await;
    if let Err(e) = is_authenticated {
        log::error!("[ROUTER:PROFILE] Error in AuthCheck: {e}");
        return Ok(());
    }
    let is_authenticated: bool = is_authenticated.unwrap();
    if is_authenticated {
        log::debug!("[ROUTER:PROFILE] AuthCheck successful!");
    } else {
        log::warn!("[ROUTER:PROFILE] AuthCheck failed! :(");
    }
    Ok(())
}

#[handler]
async fn auth_forward_to_recipe(request: &Request) -> Result<(), poem::Error> {
    log::debug!("[ROUTER:RECIPE] Recipe service called!");
    let is_authenticated: Result<bool, _> = pass_through_auth(request).await;
    if let Err(e) = is_authenticated {
        log::error!("[ROUTER:RECIPE] Error in AuthCheck: {e}");
        return Ok(());
    }
    let is_authenticated: bool = is_authenticated.unwrap();
    if is_authenticated {
        log::debug!("[ROUTER:RECIPE] AuthCheck successful!");
    } else {
        log::warn!("[ROUTER:RECIPE] AuthCheck failed! :(");
    }
    Ok(())
}

#[handler]
async fn auth_forward_to_ets(request: &Request) -> Result<(), poem::Error> {
    log::debug!("[ROUTER:ETS] ETS service called!");
    let is_authenticated: Result<bool, _> = pass_through_auth(request).await;
    if let Err(e) = is_authenticated {
        log::error!("[ROUTER:ETS] Error in AuthCheck: {e}");
        return Ok(());
    }
    let is_authenticated: bool = is_authenticated.unwrap();
    if is_authenticated {
        log::debug!("[ROUTER:ETS] AuthCheck successful!");
    } else {
        log::warn!("[ROUTER:ETS] AuthCheck failed! :(");
    }
    Ok(())
}

#[handler]
async fn auth_forward_to_menu(request: &Request) -> Result<(), poem::Error> {
    log::debug!("[ROUTER:MENU] Menu service called!");
    let is_authenticated: Result<bool, _> = pass_through_auth(request).await;
    if let Err(e) = is_authenticated {
        log::error!("[ROUTER:MENU] Error in AuthCheck: {e}");
        return Ok(());
    }
    let is_authenticated: bool = is_authenticated.unwrap();
    if is_authenticated {
        log::debug!("[ROUTER:MENU] AuthCheck successful!");
    } else {
        log::warn!("[ROUTER:MENU] AuthCheck failed! :(");
    }
    Ok(())
}

// HTTP Headers
// X-User-Uid
// HTTP Body
// The rest of the request information
//
// If user not logged in, send 401 response
// HTTP Response codes:
// -- 401: Not Logged In
// -- 403: Refresh token (send back refreshed token)
// -- 204: Response without payload
//
//
// Auth service:
// - Uses tokens
// - Input requests: Login, Logout, SingUp, Refresh Tokens
// - Tokens:
// -- Access token
// -- Refresh token
// --- GET to get -> Use path & query params for info
// --- POST to create new data -> use body for info
// --- PUT to update data
// --- DELTE tot delete data
// ---> Tokens also stored in DB
// - Auth receives both tokens for verification
fn main() {}