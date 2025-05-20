#![allow(dead_code)]

mod interfaces;

use supabase_rs::{SupabaseClient, errors::ErrorTypes as SupabaseError};
use tokio::net::TcpListener;

enum LocalPorts {
    RecipeRecommend = 5001,
    MenuRecommend = 5002,
    EatTogether = 5003,
    Profile = 5004,
}

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
    use std::net::{IpAddr, Ipv6Addr};
    log::debug!("[PROFILE] Listening for incoming requests...");
    loop {
        // Accept new incoming connection
        let (_stream, origin_address) = listener.accept().await?;
        if origin_address.ip() == IpAddr::V6(Ipv6Addr::LOCALHOST) {
            // Match call from other services
            let port: u16 = origin_address.port();
            if port == LocalPorts::RecipeRecommend as u16 {
                todo!()
            } else if port == LocalPorts::MenuRecommend as u16 {
                todo!()
            } else if port == LocalPorts::EatTogether as u16 {
                todo!()
            } else {
                log::warn!("[PROFILE] Request received from unexpected local port: {port}");
            }
        } else {
            // Match call from user/webclient
            todo!()
        }
    }
}
