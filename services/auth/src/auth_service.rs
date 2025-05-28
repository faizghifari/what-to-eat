use std::sync::Arc;

use http_body_util::BodyExt;
use hyper::{
    Request, StatusCode,
    body::{Bytes, Frame},
    header::HeaderValue,
};
use sonic_rs::{Deserialize, Serialize};
use supabase_auth::{
    error::Error as AuthError,
    models::{AuthClient, EmailSignUpResult, Session, User},
};

use super::router_service::{HttpResponse, response};

pub fn create_auth_client() -> Option<AuthClient> {
    match AuthClient::new_from_env() {
        Ok(client) => {
            log::debug!("Successfully created Supabase Auth Client.");
            Some(client)
        }
        Err(e) => {
            log::error!("Failed to create Supabase Auth Client. Reason: {e}");
            None
        }
    }
}

/// A struct to easily extract login credentials from a request body
/// Fields:
///      - email: String
///      - password: String
#[derive(Serialize, Deserialize)]
struct LoginCredentials {
    email: String,
    password: String,
}

/// The successful response struct for login or signup requests
/// Fields:
///      - `x_user_id`: Uuid,
///      - `access_token`: String,
///      - `refresh_token`: String
#[derive(Serialize, Deserialize)]
struct LoginOrSignupResponse {
    x_user_uuid: uuid::Uuid,
    access_token: String,
    refresh_token: String,
}
impl From<LoginOrSignupResponse> for hyper::body::Bytes {
    fn from(val: LoginOrSignupResponse) -> Self {
        hyper::body::Bytes::from(sonic_rs::to_vec(&val).unwrap())
    }
}
impl From<Session> for LoginOrSignupResponse {
    fn from(session: Session) -> Self {
        Self {
            x_user_uuid: session.user.id,
            access_token: session.access_token,
            refresh_token: session.refresh_token,
        }
    }
}

/// Attempts to log a user in based on the request body contents.
pub async fn login(
    mut request: Request<hyper::body::Incoming>,
    auth_client: Arc<AuthClient>,
) -> HttpResponse {
    // Read response body
    let body: Result<Vec<u8>, _> = read_body(&mut request).await;
    if let Err(e) = body {
        return e;
    }

    // Deserialise
    let login_credentials: Result<LoginCredentials, _> = sonic_rs::from_slice(&body.unwrap());
    if login_credentials.is_err() {
        return response::<&str>(
            Some("Malformed login request body"),
            StatusCode::BAD_REQUEST,
        );
    }
    let login_credentials: LoginCredentials = login_credentials.unwrap();

    // Log in
    let session: Result<Session, _> = auth_client
        .login_with_email(&login_credentials.email, &login_credentials.password)
        .await;

    if let Err(e) = session {
        return respond_to_auth_error(e);
    }
    let response_body: LoginOrSignupResponse = session.unwrap().into();

    response(Some(response_body), StatusCode::OK)
}

/// A struct containing signup credentials, to easily extract them from a request body. It takes two passwords to verify the user is aware of their input.
/// Fields:
///      - email: String
///      - `password_1`: String
///      - `password_2`: String
#[derive(Serialize, Deserialize)]
struct SignupCredentials {
    email: String,
    password_1: String,
    password_2: String,
}

pub async fn sign_up(
    mut request: Request<hyper::body::Incoming>,
    auth_client: Arc<AuthClient>,
) -> (Option<uuid::Uuid>, HttpResponse) {
    // Read response body
    let body: Result<Vec<u8>, _> = read_body(&mut request).await;
    if let Err(e) = body {
        return (None, e);
    }

    // Deserialise
    let signup_credentials: Result<SignupCredentials, _> = sonic_rs::from_slice(&body.unwrap());
    if signup_credentials.is_err() {
        return (
            None,
            response::<&str>(
                Some("Malformed signup request body"),
                StatusCode::BAD_REQUEST,
            ),
        );
    }
    let signup_credentials: SignupCredentials = signup_credentials.unwrap();

    if signup_credentials.password_1 != signup_credentials.password_2 {
        return (
            None,
            response::<&str>(Some("Passwords do not match"), StatusCode::CONFLICT),
        );
    }

    // Sign up
    let signup_result: Result<EmailSignUpResult, _> = auth_client
        .sign_up_with_email_and_password(
            &signup_credentials.email,
            &signup_credentials.password_1,
            None,
        )
        .await;
    if let Err(e) = signup_result {
        return (None, respond_to_auth_error(e));
    }

    // Check sign up response, either return or log-in
    let response_body: LoginOrSignupResponse = match signup_result.unwrap() {
        EmailSignUpResult::SessionResult(session) => session.into(),
        EmailSignUpResult::ConfirmationResult(_confirm) => {
            let session: Result<Session, _> = auth_client
                .login_with_email(&signup_credentials.email, &signup_credentials.password_1)
                .await;

            if let Err(e) = session {
                return (None, respond_to_auth_error(e));
            }

            session.unwrap().into()
        }
    };

    (
        Some(response_body.x_user_uuid),
        response(Some(response_body), StatusCode::OK),
    )
}

/// Locally logs the user out
pub async fn log_out(
    request: Request<hyper::body::Incoming>,
    auth_client: Arc<AuthClient>,
) -> HttpResponse {
    // Get access token from headers
    let access_token: Result<&str, _> = get_access_token_from_request(&request);
    if let Err(reason) = access_token {
        return response(Some(format!("{reason}")), StatusCode::BAD_REQUEST);
    }
    let access_token: &str = access_token.unwrap();

    // Log out
    let success: Result<(), _> = auth_client
        .logout(
            Some(supabase_auth::models::LogoutScope::Local),
            access_token,
        )
        .await;
    if let Err(e) = success {
        respond_to_auth_error(e)
    } else {
        response::<&str>(None, StatusCode::OK)
    }
}

/// Verifies that the user making the request is valid
/// Expects the following input format:
/// Headers:
///      - X-User-Uuid: String(uuid)
///      - Access-Token: String(token)
pub async fn verify(
    request: &Request<hyper::body::Incoming>,
    auth_client: Arc<AuthClient>,
) -> Result<(), Reason> {
    // Get Uuid
    let user_id: uuid::Uuid = get_uuid_from_request(request)?;
    let access_token: &str = get_access_token_from_request(request)?;

    // Get user info from DB
    let user: Result<User, _> = auth_client.get_user(access_token).await;
    if user.is_ok_and(|user| user.id == user_id) {
        Ok(())
    } else {
        Err(Reason::InvalidCredentials)
    }
}

/// Get user UID from Query heaaders and convert to Uuid
fn get_uuid_from_request(request: &Request<hyper::body::Incoming>) -> Result<uuid::Uuid, Reason> {
    let uuid_header: Option<&HeaderValue> = request.headers().get("X-User-Uuid");
    if uuid_header.is_none() {
        return Err(Reason::InvalidUserId);
    }
    let user_id: Result<&str, _> = uuid_header.unwrap().to_str();
    if user_id.is_err() {
        return Err(Reason::InvalidUserId);
    }
    let user_id: Result<uuid::Uuid, _> = uuid::Uuid::parse_str(user_id.unwrap());
    if let Ok(user_id) = user_id {
        Ok(user_id)
    } else {
        Err(Reason::InvalidUserId)
    }
}

fn get_access_token_from_request(request: &Request<hyper::body::Incoming>) -> Result<&str, Reason> {
    let access_token: Option<&HeaderValue> = request.headers().get("Access-Token");
    if access_token.is_none() {
        return Err(Reason::InvalidAccessToken);
    }
    let access_token: Result<&str, _> = access_token.unwrap().to_str();
    if access_token.is_err() {
        return Err(Reason::InvalidAccessToken);
    }
    Ok(access_token.unwrap())
}

/// A utility function to extract the body contents from a request
async fn read_body(request: &mut Request<hyper::body::Incoming>) -> Result<Vec<u8>, HttpResponse> {
    // Read body stream
    let mut body: Vec<u8> = Vec::with_capacity(64);
    while let Some(next) = request.frame().await {
        let frame: Result<Frame<Bytes>, _> = next;
        if frame.is_err() {
            return Err(response::<&str>(None, StatusCode::INTERNAL_SERVER_ERROR));
        }
        body.extend_from_slice(frame.unwrap().data_ref().unwrap());
    }
    Ok(body)
}

/// Provides appropriate HTTP response to an Authentication error
fn respond_to_auth_error(e: AuthError) -> HttpResponse {
    match e {
        AuthError::InternalError
        | AuthError::NetworkError(_)
        | AuthError::ParseUrlError
        | AuthError::Supabase(_) => response::<&str>(None, StatusCode::INTERNAL_SERVER_ERROR),
        err => response(Some(format!("{err}")), StatusCode::UNAUTHORIZED),
    }
}

#[allow(clippy::enum_variant_names)]
#[derive(Debug)]
pub enum Reason {
    InvalidCredentials,
    InvalidUserId,
    InvalidAccessToken,
}
impl std::fmt::Display for Reason {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Reason::InvalidCredentials => write!(f, "Invalid Credentials"),
            Reason::InvalidUserId | Reason::InvalidAccessToken => write!(f, "Invalid Headers"),
        }
    }
}
