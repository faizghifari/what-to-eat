use hyper::{
    HeaderMap, Method, Request, Response, StatusCode,
    body::Bytes,
    client::conn::http1::{Connection, SendRequest, handshake},
    server::conn::http1,
    service::service_fn,
};
use hyper_util::rt::TokioIo;
use std::{convert::Infallible, net::SocketAddr, sync::Arc};
use supabase_auth::models::AuthClient;
use tokio::net::TcpStream;

use super::auth_service as auth;

pub async fn run() {
    log::debug!("Started");

    let auth_client: Option<AuthClient> = super::auth_service::create_auth_client();
    if auth_client.is_none() {
        return;
    }

    receiver(None, None, Arc::new(auth_client.unwrap())).await;
}

/// Listens to incoming connections and then passes them to relevant service to be processed.
/// Takes the address and port of the socket to listen to as input parameters. Defaults to LOCALHOST:5000.
/// Also takes ownership of a provided Supabase Authentication Client
async fn receiver(
    address: Option<std::net::IpAddr>,
    port: Option<u16>,
    auth_client: Arc<AuthClient>,
) {
    use tokio::net::TcpListener;

    let listener: Result<TcpListener, _> = TcpListener::bind((
        address.unwrap_or(std::net::IpAddr::V4(std::net::Ipv4Addr::UNSPECIFIED)), // listen on 0.0.0.0
        port.unwrap_or(8000), // changed from 5000 to 8000
    ))
    .await;

    if let Err(e) = listener {
        log::error!("Failed to bind Tcp Listener to socket. Reason: {e}");
        return;
    }

    let listener: TcpListener = listener.unwrap();

    // Continuously accpet incoming connections
    loop {
        // Accept new connection
        let incoming: Result<(TcpStream, SocketAddr), _> = listener.accept().await;
        if let Err(e) = incoming {
            log::warn!("Failed to accept incoming connection. Reason: {e}");
            continue;
        }
        let (stream, _source): (TcpStream, SocketAddr) = incoming.unwrap();
        // Convert TcpStream to TokioIO to access hyper traits
        let io: TokioIo<_> = TokioIo::new(stream);

        // Spawn a new asynchronous tokio task to serve multiple connections asynchronously
        let local_auth_client: Arc<AuthClient> = auth_client.clone();
        tokio::task::spawn(async move {
            // Bind incoming connection to router service
            if let Err(e) = http1::Builder::new()
                .serve_connection(
                    io,
                    service_fn(move |request| auth_router(request, local_auth_client.clone())),
                )
                .await
            {
                log::warn!("Error serving connection: {e}");
            }
        });
    }
}

/// Utility type alias for HTTP responses
pub type HttpResponse = Result<Response<BoxBody<Bytes, hyper::Error>>, Infallible>;

/// Router function, forwards Auth requests to the relevant functions, verifies user identification info for other requests. Then passes them to the general router.
async fn auth_router(
    request: Request<hyper::body::Incoming>,
    auth_client: Arc<AuthClient>,
) -> HttpResponse {
    match (
        request.method().clone(),
        request.uri().path().to_owned().as_str(),
    ) {
        (Method::POST, "/auth/login") => auth::login(request, auth_client).await,
        (Method::POST, "/auth/signup") => auth::sign_up(request, auth_client).await,
        (Method::POST, "/auth/logout") => auth::log_out(request, auth_client).await,
        (method, path) => router(request, &method, path, auth_client).await,
    }
}

/// General router, selects relevant service based on Request URI
async fn router(
    request: Request<hyper::body::Incoming>,
    method: &Method,
    path: &str,
    auth_client: Arc<AuthClient>,
) -> HttpResponse {
    let mut path_components: std::str::SplitTerminator<'_, char> = path.split_terminator('/');
    path_components.next();
    let target: Option<&str> = path_components.next();

    if target.is_none() {
        return bad_request(method, path);
    }

    let target: Target = match target.unwrap() {
        "profile" => Target::Profile,
        "recipe" => Target::Recipe,
        "menu" => Target::Menu,
        "restaurant" => Target::Menu,
        "eat-together" => Target::ETS,
        _ => return bad_request(method, path),
    };

    log::info!("Checkpoint 1, {target:?} authorizing request...");

    let authorised: Result<(), auth::Reason> = auth::verify(&request, auth_client).await;
    if let Err(reason) = authorised {
        log::warn!("Unauthorised access attempt. Authentication failure reason: {reason}");
        return response(Some(format!("{reason}")), StatusCode::UNAUTHORIZED);
    }

    log::info!("Received request for {target:?} service. Method: {method} | Path: {path}");

    forward_to_service(target, request).await
}

/// Forwarding function, forwards the request to the relevant service and waits for an answer
async fn forward_to_service(
    target: Target,
    request: Request<hyper::body::Incoming>,
) -> HttpResponse {
    // Get request's intended destination
    let (url, port): (&str, u16) = match target {
        Target::Profile => ("http://profile-service", 8000),
        Target::Recipe => ("http://recipe-service", 8000),
        Target::Menu => ("http://menu-service", 8000),
        Target::ETS => ("http://ets-service", 8000),
    };

    // Convert URL into Hyper-compatible URL
    let uri: hyper::Uri = url
        .parse::<hyper::Uri>()
        .expect("This error cannot happen.");
    let host: Option<&str> = uri.host();

    // This should not be an error, but just in case
    if host.is_none() {
        log::error!("Invalid forwarding URL: {url}");
        return response::<&str>(None, StatusCode::INTERNAL_SERVER_ERROR);
    }

    let host: &str = host.unwrap();
    let address: String = format!("{host}:{port}");

    // Open a TCP connection to destination
    let stream: Result<TcpStream, _> = TcpStream::connect(address).await;
    if let Err(e) = stream {
        log::error!("Failed to connect to {uri}. Reason: {e}");
        return response::<&str>(None, StatusCode::INTERNAL_SERVER_ERROR);
    }
    let io: TokioIo<TcpStream> = TokioIo::new(stream.unwrap());

    // Create HTTP Client
    let handshake_success: Result<_, _> =
        handshake::<TokioIo<TcpStream>, hyper::body::Incoming>(io).await;
    if let Err(e) = handshake_success {
        log::error!("Failed to establish handshake with {uri}. Reason: {e}");
        return response::<&str>(None, StatusCode::INTERNAL_SERVER_ERROR);
    }
    let (mut sender, conn): (SendRequest<_>, Connection<_, _>) = handshake_success.unwrap();

    if let Err(e) = conn.await {
        log::error!("Failed to connect with {uri}. Reason: {e}");
        return response::<&str>(None, StatusCode::INTERNAL_SERVER_ERROR);
    }

    // Forward request and wait for response
    let incoming_response: Result<_, _> = sender.send_request(request).await;
    if let Err(e) = incoming_response {
        log::error!("Failed to get response from forwarded request. Reason: {e}");
        return response::<&str>(None, StatusCode::INTERNAL_SERVER_ERROR);
    }

    // Translate incoming response to outgoing response
    let received_response: Response<hyper::body::Incoming> = incoming_response.unwrap();
    let status: StatusCode = received_response.status();
    let headers: HeaderMap = received_response.headers().clone();
    let body: BoxBody<_, _> = received_response.boxed();

    let mut outgoing_response: Response<_> = Response::new(body);
    *outgoing_response.status_mut() = status;
    *outgoing_response.headers_mut() = headers;
    Ok(outgoing_response)
}

#[allow(clippy::upper_case_acronyms)]
#[derive(Debug)]
enum Target {
    Profile,
    Recipe,
    Menu,
    ETS,
}

// Utilities
use http_body_util::{BodyExt, Empty, Full, combinators::BoxBody};
/// Utility function to turn a chunk of data into a Full body.
pub fn empty() -> BoxBody<Bytes, hyper::Error> {
    Empty::<Bytes>::new()
        .map_err(|never| match never {})
        .boxed()
}
/// Utility function to turn a cunk of data into an Empty body
pub fn full<T: Into<Bytes>>(chunk: T) -> BoxBody<Bytes, hyper::Error> {
    Full::new(chunk.into())
        .map_err(|never| match never {})
        .boxed()
}

/// Utility function to return `BAD_REQUEST` in case of an invalid request path or method
pub fn bad_request(method: &Method, path: &str) -> HttpResponse {
    log::warn!("Received request with invalid method or path. Method: {method} | Path: {path}");

    let mut bad_request: Response<_> = Response::new(full(format!(
        "Cannot use {method} method with path: {path}"
    )));
    *bad_request.status_mut() = StatusCode::BAD_REQUEST;
    Ok(bad_request)
}

/// Utility function to create a simple HTTP response
pub fn response<T: Into<Bytes>>(message: Option<T>, code: StatusCode) -> HttpResponse {
    match message {
        None => {
            let mut response: Response<_> = Response::new(empty());
            *response.status_mut() = code;
            Ok(response)
        }
        Some(msg) => {
            let mut response: Response<_> = Response::new(full(msg));
            *response.status_mut() = code;
            Ok(response)
        }
    }
}
