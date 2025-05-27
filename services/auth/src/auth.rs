// Auth service

use interprocess::local_socket::{
    GenericNamespaced, ListenerOptions, Name, ToNsName,
    tokio::{Listener, Stream},
    traits::tokio::{Listener as ListenerTrait, Stream as StreamTrait},
};
use serde::{Deserialize, Serialize};
use supabase_auth::{
    error::Error as AuthError,
    models::{AuthClient, EmailSignUpResult, Session},
};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

pub const AUTH_SOCKET_PRINTNAME: &str = "w2e_auth.sock";
pub async fn run() -> std::io::Result<()> {
    // Authenticate service with Supabase / launch client
    let client: Result<AuthClient, _> = init_supabase_auth_client();
    if let Err(e) = client {
        log::error!("[AUTH] Failed to create Supabase client: {e}");
        return Err(std::io::Error::new(
            std::io::ErrorKind::PermissionDenied,
            "Failed to authenticate Supabase client: {e}",
        ));
    }
    let client: AuthClient = client.unwrap();
    log::debug!("[AUTH] Created SupabaseClient successfully!");

    launch_listener(&client).await?;

    Ok(())
}

fn init_supabase_auth_client() -> Result<AuthClient, &'static str> {
    let supabase_url: &'static str = env!("SUPABASE_URL");
    let supabase_key: &'static str = env!("SUPABASE_KEY");
    let supabase_jwt: &'static str = env!("SUPABASE_JWT");
    if supabase_key.is_empty() || supabase_url.is_empty() {
        log::warn!("[AUTH] Failed to read API creds correctly!");
        Err("Could not read credentials.")
    } else {
        Ok(AuthClient::new(supabase_url, supabase_key, supabase_jwt))
    }
}
#[derive(serde::Serialize, serde::Deserialize, Debug)]
pub enum AuthQueryType {
    Login,
    SignUp,
    Logout,
    Validate,
    Unknown,
}

pub async fn create_auth_stream() -> std::io::Result<Stream> {
    // Pick socket name
    let socket_name: Name = AUTH_SOCKET_PRINTNAME.to_ns_name::<GenericNamespaced>()?;
    let stream: Stream = Stream::connect(socket_name).await?;
    Ok(stream)
}

pub async fn send_to_auth<'a>(
    stream: &'a Stream,
    data: &[u8],
) -> std::io::Result<BufReader<&'a Stream>> {
    log::debug!("[ROUTER] Sending to Auth service.");
    let receiver: BufReader<&Stream> = BufReader::new(stream);
    let mut sending_stream: &Stream = stream;
    if let Err(e) = sending_stream.write_all(data).await {
        log::error!("[ROUTER] Failed to send data to Auth:. {e}");
    }
    log::debug!("[ROUTER] Payload for Auth service sent succssfully!");

    Ok(receiver)
}

pub async fn launch_listener(client: &AuthClient) -> std::io::Result<()> {
    log::debug!("[AUTH] Creating local socket listener...");
    // Pick socket name
    let socket_name: Name = AUTH_SOCKET_PRINTNAME.to_ns_name::<GenericNamespaced>()?;
    // Configure listener
    let options: ListenerOptions = ListenerOptions::new().name(socket_name);
    // Create listener
    let listener: Listener = match options.create_tokio() {
        Err(e) if e.kind() == std::io::ErrorKind::AddrInUse => {
            log::error!("[AUTH] Local socket already occupied");
            return Err(e);
        }
        listener => listener?,
    };
    log::debug!("[AUTH] Local socket created successfully.");

    // Setup loop to process incoming connections
    loop {
        let incoming: Stream = listener.accept().await?;
        let local_client: AuthClient = client.clone();
        tokio::spawn(async move {
            log::debug!("[AUTH] Processing incoming request in seperate thread.");
            if let Err(e) = process_stream(incoming, local_client).await {
                log::error!("[AUTH] Error while handling incoming connection. {e}");
            }
        });
    }
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SignupInfo {
    email: String,
    password: String,
    password2: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct LoginInfo {
    email: String,
    password: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct AuthInfo {
    x_user_uid: String,
    access_token: String,
    refresh_token: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SignupOrLoginResponse {
    pub access_token: String,
    pub refresh_token: String,
    pub x_user_uid: String,
}
impl SignupOrLoginResponse {
    fn from_session(session: Session) -> Self {
        Self {
            x_user_uid: session
                .user
                .id
                .hyphenated()
                .encode_lower(&mut uuid::Uuid::encode_buffer())
                .to_string(),
            access_token: session.access_token,
            refresh_token: session.refresh_token,
        }
    }

    async fn from_signup_result(
        signup_result: EmailSignUpResult,
        signup_info: &SignupInfo,
        client: &AuthClient,
    ) -> Option<Self> {
        match signup_result {
            EmailSignUpResult::SessionResult(session) => Some(Self {
                access_token: session.access_token,
                refresh_token: session.refresh_token,
                x_user_uid: session
                    .user
                    .id
                    .as_hyphenated()
                    .encode_lower(&mut uuid::Uuid::encode_buffer())
                    .to_string(),
            }),
            EmailSignUpResult::ConfirmationResult(_) => {
                let session: Result<Session, AuthError> = client
                    .login_with_email(&signup_info.email, &signup_info.password)
                    .await;

                if let Ok(session) = session {
                    log::debug!("[AUTH:LOGIN] Successfully logged in! Session: {session:#?}");
                    Some(SignupOrLoginResponse::from_session(session))
                } else {
                    None
                }
            }
        }
    }
}

#[derive(Serialize, Deserialize, Debug)]
pub struct AuthResponse {}

async fn process_stream(stream: Stream, client: AuthClient) -> std::io::Result<()> {
    let mut receiver: BufReader<&Stream> = BufReader::new(&stream);
    let sender: &Stream = &stream;

    log::debug!("[AUTH] Processing...");

    let mut msg: Vec<u8> = Vec::with_capacity(256);
    let _ = receiver.read_until(u8::MAX, &mut msg).await;

    if msg.is_empty() {
        log::warn!("Auth received empty message!");
        return Ok(());
    }

    let request_type: AuthQueryType = match msg.remove(0) {
        1 => AuthQueryType::SignUp,
        2 => AuthQueryType::Login,
        3 => AuthQueryType::Logout,
        4 => AuthQueryType::Validate,
        _ => AuthQueryType::Unknown,
    };
    if msg.last().unwrap() == &u8::MAX {
        let _ = msg.pop();
    }

    log::debug!("[AUTH] Query type identified, calling relevant module");
    match request_type {
        AuthQueryType::Login => login(&msg, client, sender).await,
        AuthQueryType::SignUp => sign_up(&msg, client, sender).await,
        AuthQueryType::Logout => logout(&msg, client).await,
        AuthQueryType::Validate => is_valid_user(&msg, client, sender).await,
        AuthQueryType::Unknown => log::warn!("Unsupported Auth request!"),
    };

    log::info!("[AUTH] Processed!");
    Ok(())
}

async fn login(bytes: &[u8], client: AuthClient, mut stream: &Stream) {
    log::debug!("[AUTH:LOGIN] Login function called!");
    match serde_cbor::from_slice::<LoginInfo>(bytes) {
        Err(e) => log::error!("[AUTH:LOGIN] Failed to deserialise Login info: {e}"),
        Ok(login_info) => {
            log::debug!("[AUTH:LOGIN] Deserialised successfully!: {login_info:#?}");

            // Login to supabase
            let session: Result<Session, AuthError> = client
                .login_with_email(&login_info.email, &login_info.password)
                .await;

            if let Ok(session) = session {
                log::debug!("[AUTH:LOGIN] Successfully logged in! Session: {session:#?}");
                if let Ok(data) = serde_cbor::to_vec(&SignupOrLoginResponse::from_session(session))
                {
                    if let Err(e) = stream.write_all(&data).await {
                        log::error!("[AUTH:LOGIN] Failed to send response to Router: {e}");
                    }
                } else {
                    log::error!("[AUTH:LOGIN] Failed to serialise Login response.")
                }
            } else if let Err(e) = session {
                log::error!("[AUTH:LOGIN] Failed to log in: {e}");
            }
        }
    }
}

async fn sign_up(bytes: &[u8], client: AuthClient, mut stream: &Stream) {
    log::debug!("[AUTH:SIGNUP] Sign Up function called!");
    match serde_cbor::from_slice::<SignupInfo>(bytes) {
        Err(e) => log::error!("[AUTH:SIGNUP] Failed to deserialise SignUp info: {e}"),
        Ok(signup_info) => {
            log::debug!("[AUTH:SIGNUP] Deserialised successfully!: {signup_info:#?}");

            // Sign up with supabase
            let success: Result<EmailSignUpResult, AuthError> = client
                .sign_up_with_email_and_password(&signup_info.email, &signup_info.password, None)
                .await;

            if let Ok(signup_result) = success {
                log::debug!("[AUTH:SIGNUP] Signed up successfully: {signup_result:#?}");
                if let Ok(data) = serde_cbor::to_vec(
                    &SignupOrLoginResponse::from_signup_result(
                        signup_result,
                        &signup_info,
                        &client,
                    )
                    .await
                    .unwrap_or_else(|| {
                        log::warn!("[AUTH:SIGNUP] Failed to get Auth info.");
                        SignupOrLoginResponse {
                            access_token: "".to_string(),
                            refresh_token: "".to_string(),
                            x_user_uid: "".to_string(),
                        }
                    }),
                ) {
                    if let Err(e) = stream.write_all(&data).await {
                        log::error!("[AUTH:SIGNUP] Failed to send response to Router: {e}");
                    }
                } else {
                    log::error!("[AUTH:SIGNUP] Failed to serialise Signup response.")
                }
            } else if let Err(e) = success {
                log::error!("[AUTH:SIGNUP] Failed to sign up: {e}");
            }
        }
    }
}

async fn logout(_bytes: &[u8], _client: AuthClient) {
    log::debug!("Logout function called!");
}

#[derive(Serialize, Deserialize)]
pub struct UserTokens {
    pub x_user_uid: String,
    pub access_token: String,
    pub refresh_token: String,
}

async fn is_valid_user(bytes: &[u8], client: AuthClient, mut stream: &Stream) {
    log::debug!("[AUTH:VALIDATE] User validation check requested!");
    let response: Result<bool, String> = match serde_cbor::from_slice::<AuthInfo>(bytes) {
        Err(e) => {
            log::error!("[AUTH:VALIDATE] Failed to deserialise AuthInfo: {e}");
            Err(format!("Failed to deserialise AuthInfo: {e}"))
        }
        Ok(auth_info) => {
            log::debug!("[AUTH:VALIDATE] Deserialised successfully!");
            let user = client.get_user(&auth_info.access_token).await;
            match user {
                Err(e) => {
                    log::error!("[AUTH:VALIDATE] Failed to get user: {e}");
                    Ok(false)
                }
                Ok(user) => {
                    if user
                        .id
                        .hyphenated()
                        .encode_lower(&mut uuid::Uuid::encode_buffer())
                        == &auth_info.x_user_uid
                    {
                        log::debug!("[AUTH:VALIDATE] Authentication successful!");
                        Ok(true)
                    } else {
                        log::warn!("[AUTH:VALIDATE] Access token and user UUID don't match!");
                        Ok(false)
                    }
                }
            }
        }
    };

    let data: Vec<u8> = serde_cbor::to_vec(&response).unwrap_or_else(|_| {
        log::error!("[AUTH:VALIDATE] Failed to serialise validation response!");
        vec![]
    });
    if let Err(e) = stream.write_all(&data).await {
        log::error!("[AUTH:VALIDATE] Failed to send response to Router: {e}");
    }
}
