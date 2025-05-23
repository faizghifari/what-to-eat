use interprocess::local_socket::tokio::Stream as LocalStream;
use poem::{Body, Request, Route, Server, get, handler, listener::TcpListener, post};
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
        log::debug!("[GATEKEEPR] Created tokio runtime successfully!");
        // Run concurrent and parallel systems
        runtime.block_on(run_combined_system())
    } else {
        log::error!("[GATEKEEPR] Failed to create Tokio runtime!");
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
        log::error!("[GATEKEEPR] Failed to start parallel auth, profile and server services: {e}");
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

#[handler]
async fn auth_signup(body: Body) -> Result<(), poem::Error> {
    log::debug!("[ROUTER] Signup request received. Rerouting!");

    if let Ok(signup_info) = body.into_json::<subservices::auth::SignupInfo>().await {
        log::debug!("[ROUTER] Grabbed request body.");

        let mut message: Vec<u8> = vec![1];
        message.extend_from_slice(&serde_cbor::to_vec(&signup_info).unwrap_or_else(|_| {
            log::error!("Failed to reserialise signup info.");
            vec![]
        }));
        message.push(u8::MAX);

        let stream: Result<LocalStream, _> = subservices::auth::create_auth_stream().await;
        if let Err(e) = stream {
            log::error!("[ROUTER] Failed to connect to Auth service: {e}");
            return Err(poem::Error::from_string(
                "Router failed to connect to Auth service",
                poem::http::StatusCode::SERVICE_UNAVAILABLE,
            ));
        }
        let stream: LocalStream = stream.unwrap();

        match subservices::auth::send_to_auth(&stream, &message).await {
            Err(e) => {
                log::error!("[ROUTER] Failed to send Signup request to Auth service: {e}");
                Err(poem::Error::from_string(
                    "Router failed to send signup request to Auth service",
                    poem::http::StatusCode::SERVICE_UNAVAILABLE,
                ))
            }
            Ok(mut stream) => {
                let mut response_buffer: Vec<u8> = Vec::with_capacity(512);
                if let Err(e) = stream.read_to_end(&mut response_buffer).await {
                    log::error!("[ROUTER] Failed to read signup response: {e}");
                }
                if let Ok(response) =
                    serde_cbor::from_slice::<subservices::auth::SignupResponse>(&response_buffer)
                {
                    log::debug!("[ROUTER] Received response from signup: {response:#?}");
                } else {
                    log::error!("[ROUTER] Failedd to deserialise signup response");
                }
                Ok(())
            }
        }
    } else {
        log::error!("[ROUTER] Failed to deserialise Signup request contents!");
        Ok(())
    }
}

#[handler]
async fn auth_login(body: Body) -> poem::Result<()> {
    log::debug!("[ROUTER] Signup request received. Rerouting!");

    if let Ok(login_info) = body.into_json::<subservices::auth::LoginInfo>().await {
        log::debug!("[ROUTER] Grabbed request body: {login_info:#?}");

        let mut message: Vec<u8> = vec![2];
        message.extend_from_slice(&serde_cbor::to_vec(&login_info).unwrap_or_else(|_| {
            log::error!("Failed to reserialise signup info.");
            vec![]
        }));
        message.push(u8::MAX);

        let stream: Result<LocalStream, _> = subservices::auth::create_auth_stream().await;
        if let Err(e) = stream {
            log::error!("[ROUTER] Failed to connect to Auth service: {e}");
            return Err(poem::Error::from_string(
                "Router failed to connect to Auth service",
                poem::http::StatusCode::SERVICE_UNAVAILABLE,
            ));
        }
        let stream: LocalStream = stream.unwrap();

        match subservices::auth::send_to_auth(&stream, &message).await {
            Err(e) => {
                log::error!("[ROUTER] Failed to send Signup request to Auth service: {e}");
                Err(poem::Error::from_string(
                    "Router failed to send signup request to Auth service",
                    poem::http::StatusCode::SERVICE_UNAVAILABLE,
                ))
            }
            Ok(mut stream) => {
                let mut response_buffer: Vec<u8> = Vec::with_capacity(512);
                if let Err(e) = stream.read_to_end(&mut response_buffer).await {
                    log::error!("[ROUTER] Failed to read signup response: {e}");
                }
                if let Ok(response) =
                    serde_cbor::from_slice::<subservices::auth::SignupResponse>(&response_buffer)
                {
                    log::debug!("[ROUTER] Received response from signup: {response:#?}");
                } else {
                    log::error!("[ROUTER] Failedd to deserialise signup response");
                }
                Ok(())
            }
        }
    } else {
        log::error!("[ROUTER] Failed to deserialise Signup request contents!");
        Ok(())
    }
}

#[handler]
async fn auth_forward_to_profile(_request: &Request, _body: Body) {
    log::debug!("[ROUTER] Profile service called!");
}

#[handler]
async fn auth_forward_to_recipe() {
    log::debug!("[ROUTER] Recipe service called!")
}

#[handler]
async fn auth_forward_to_ets() {
    log::debug!("[ROUTER] ETS service called!")
}

#[handler]
async fn auth_forward_to_menu() {
    log::debug!("[ROUTER] Menu service called!")
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
