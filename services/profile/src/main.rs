#![allow(dead_code)]
#![feature(ascii_char)]

mod interfaces;

use supabase_rs::{SupabaseClient, errors::ErrorTypes as SupabaseError};
use tokio::net::{TcpListener, TcpStream};

enum LocalPorts {
    RecipeRecommend = 5001,
    MenuRecommend = 5002,
    EatTogether = 5003,
    Profile = 5004,
}

#[derive(PartialEq, Eq)]
enum RequestCodes {
    GetProfile = 100,
    EditProfile = 200,
    GetPreferences = 300,
    GetRestrictions = 400,
    GetTools = 500,
    GetIngredients = 600,
    GetLocation = 700,
}

fn main() {
    // Initiate logger with relevant level
    #[cfg(debug_assertions)]
    simple_logger::init_with_level(log::Level::Debug).unwrap();
    #[cfg(not(debug_assertions))]
    simple_logger::init_with_level(log::Level::Info).unwrap();

    if let Ok(client) = create_supabase_client() {
        log::debug!("[PROFILE] Created Supabase client!");
        // Create tokio runtime to block asynchronouse loop
        use tokio::runtime::Runtime;
        if let Ok(runtime) = Runtime::new() {
            log::debug!("[PROFILE] Created tokio runtime successfully!");
            runtime.block_on(profile_runner(&client));
        } else {
            log::error!("[PROFILE] Failed to create Tokio runtime!");
        }
    } else {
        log::error!("[PROFILE] Failed to create Supabase client!");
    }
}

/// Reads supabase auth credentials from file, returns an errors if it fails
fn create_supabase_client() -> Result<SupabaseClient, SupabaseError> {
    const SUPABASE_CREDS: &str = "../sb.uk";

    if let Ok(mut file) = std::fs::File::open(SUPABASE_CREDS) {
        use std::io::Read;

        let mut contents: String = String::new();
        let _ = file.read_to_string(&mut contents);
        if contents.is_empty() {
            log::warn!("[PROFILE] Supabase API creds missing!");
            Err(SupabaseError::ApiKeyMissing)
        } else {
            let mut lines: std::str::Lines = contents.lines();
            let supabase_url: String = lines.next().unwrap_or("").to_string();
            let supabase_key: String = lines.next().unwrap_or("").to_string();

            if supabase_key.is_empty() || supabase_url.is_empty() {
                log::warn!("[PROFILE] Failed to read API creds correctly!");
                Err(SupabaseError::ApiKeyMissing)
            } else {
                SupabaseClient::new(supabase_url, supabase_key)
            }
        }
    } else {
        log::warn!("[PROFILE] Could not find API creds file!");
        Err(SupabaseError::ApiKeyMissing)
    }
}

async fn profile_runner(_client: &SupabaseClient) {
    use std::net::Ipv6Addr;

    // Listen for calls to Profile service socket
    const PROFILE_SOCKET: (Ipv6Addr, u16) = (Ipv6Addr::LOCALHOST, 5004);
    if let Ok(listener) = TcpListener::bind(PROFILE_SOCKET).await {
        log::debug!("[PROFILE] Bound to socket successfully!");
        manage_listener(&listener).await;
    } else {
        log::error!("[PROFILE] Failed to bind to socket.");
    }
}

async fn manage_listener(listener: &TcpListener) {
    if let Err(e) = process_requests(listener).await {
        log::warn!("[PROFILE] Error encountered when processing Profile service request: {e:#?}");
        // Have to box the new async function to avoid an infinite size Future
        Box::pin(manage_listener(listener)).await;
    }
}

async fn process_requests(listener: &TcpListener) -> std::io::Result<()> {
    use std::net::SocketAddr;
    log::debug!("[PROFILE] Listening for incoming requests...");
    loop {
        // Accept new incoming connection
        let (stream, origin_address): (TcpStream, SocketAddr) = listener.accept().await?;

        // Read stream
        let mut message: String = String::new();

        loop {
            // Wait for socket to be readable
            stream.readable().await?;

            // Try to read the data, could still fail if readable false positive
            let mut buf: [u8; 64] = [0; 64];
            match stream.try_read(&mut buf) {
                Ok(0) => {
                    log::debug!("[PROFILE] Finished reading stream!");
                    if let Some(ascii_slice) = buf.as_ascii() {
                        message.push_str(ascii_slice.as_str());
                    }
                    break;
                }
                Ok(n) => {
                    log::debug!("[PROFILE] Read {n} bytes from incoming stream");
                    if let Some(ascii_slice) = buf.as_ascii() {
                        message.push_str(ascii_slice.as_str());
                    }
                }
                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    continue;
                }
                Err(e) => {
                    return Err(e);
                }
            }
        }

        // Parse message
        if message.is_empty() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "[PROFILE] Incoming stream empty!",
            ));
        }
        let mut split_message = message.split_terminator("#id#");
        let request_code: isize = split_message
            .next()
            .unwrap_or("0")
            .parse::<isize>()
            .unwrap_or(-1);

        let user_id: u32 = split_message
            .next()
            .unwrap_or("0")
            .parse::<u32>()
            .unwrap_or(0);

        if origin_address.ip() == listener.local_addr()?.ip() {
            // Match request call from other services
            match request_code {
                request if request == RequestCodes::GetProfile as isize => {
                    log::debug!("[PROFILE] Received GetProfile request");
                }
                request if request == RequestCodes::GetPreferences as isize => {
                    log::debug!("[PROFILE] Received GetPreferences request");
                }
                request if request == RequestCodes::GetRestrictions as isize => {
                    log::debug!("[PROFILE] Received GetRestrictions request");
                }
                request if request == RequestCodes::GetTools as isize => {
                    log::debug!("[PROFILE] Received GetTools request");
                }
                request if request == RequestCodes::GetIngredients as isize => {
                    log::debug!("[PROFILE] Received GetIngredients request");
                }
                request if request == RequestCodes::GetLocation as isize => {
                    log::debug!("[PROFILE] Received GetLocation request");
                }
                request if request == RequestCodes::EditProfile as isize => {
                    log::debug!("[PROFILE] Received EditProfile request");
                }
                request => log::warn!("[PROFILE] Received unsupported request code: {request}"),
            }
        } else {
            // Match call from user/webclient
            log::debug!("[PROFILE] Received request from external address!");
        }
    }
}

struct Profile {
    uid: u32,
    preferences: Vec<String>,
    restrictions: Vec<String>,
    tools: Vec<String>,
    ingredients: Vec<String>,
    location: Vec<String>,
}

fn fetch_profile(_user_id: u32, _client: &SupabaseClient) -> Option<Profile> {
    None
}
