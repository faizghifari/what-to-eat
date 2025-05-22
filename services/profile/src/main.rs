#![allow(dead_code)]
#![feature(ascii_char)]

mod interfaces;

use std::collections::HashMap;

use supabase_rs::{SupabaseClient, errors::ErrorTypes as SupabaseError};
use tokio::net::{TcpListener, TcpStream};

const LOCALHOST: std::net::Ipv6Addr = std::net::Ipv6Addr::LOCALHOST;

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

async fn profile_runner(client: &SupabaseClient) {
    use std::net::Ipv6Addr;

    // Listen for calls to Profile service socket
    const PROFILE_SOCKET: (Ipv6Addr, u16) = (LOCALHOST, 5004);
    if let Ok(listener) = TcpListener::bind(PROFILE_SOCKET).await {
        log::debug!("[PROFILE] Bound to socket successfully!");
        manage_listener(&listener, client).await;
    } else {
        log::error!("[PROFILE] Failed to bind to socket.");
    }
}

async fn manage_listener(listener: &TcpListener, client: &SupabaseClient) {
    if let Err(e) = process_requests(listener, client).await {
        log::warn!("[PROFILE] Error encountered when processing Profile service request: {e:#?}");
        // Have to box the new async function to avoid an infinite size Future
        Box::pin(manage_listener(listener, client)).await;
    }
}

async fn process_requests(listener: &TcpListener, client: &SupabaseClient) -> std::io::Result<()> {
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

        let user_id: &str = split_message
            .next()
            .unwrap_or("00000000-0000-0000-0000-000000000000");

        if origin_address.ip() == listener.local_addr()?.ip() {
            // Match request call from other services
            let mut get_single_attribute: bool = false;
            let mut attribute: &[ProfileAttribute] = &[ProfileAttribute::Unknown];
            match request_code {
                request if request == RequestCodes::GetProfile as isize => {
                    log::debug!("[PROFILE] Received GetProfile request");
                    if let Err(e) = fetch_profile(user_id, client).await {
                        log::error!("[PROFILE] Failed to fetch profile:\n{e}");
                    }
                }
                request if request == RequestCodes::GetPreferences as isize => {
                    log::debug!("[PROFILE] Received GetPreferences request");
                    attribute = &[ProfileAttribute::Preferences];
                    get_single_attribute = true;
                }
                request if request == RequestCodes::GetRestrictions as isize => {
                    log::debug!("[PROFILE] Received GetRestrictions request");
                    attribute = &[ProfileAttribute::Restrictions];
                    get_single_attribute = true;
                }
                request if request == RequestCodes::GetTools as isize => {
                    log::debug!("[PROFILE] Received GetTools request");
                    attribute = &[ProfileAttribute::Tools];
                    get_single_attribute = true;
                }
                request if request == RequestCodes::GetIngredients as isize => {
                    log::debug!("[PROFILE] Received GetIngredients request");
                    attribute = &[ProfileAttribute::Ingredients];
                    get_single_attribute = true;
                }
                request if request == RequestCodes::GetLocation as isize => {
                    log::debug!("[PROFILE] Received GetLocation request");
                    log::error!("[PROFILE] Location request not yet implemented!");
                }
                request if request == RequestCodes::EditProfile as isize => {
                    log::debug!("[PROFILE] Received EditProfile request");
                    log::error!("[PROFILE] Profile editing not yet implemented!");
                }
                request => log::warn!("[PROFILE] Received unsupported request code: {request}"),
            }

            if get_single_attribute {
                let output: HashMap<ProfileAttribute, HashMap<String, String>> =
                    match read_profile_attributes(user_id, attribute, client).await {
                        Ok(output) => Ok(output),
                        Err(e) => Err(std::io::Error::new(
                            std::io::ErrorKind::InvalidData,
                            format!("Failed to get attribute {attribute:?}: {e}"),
                        )),
                    }?;

                log::debug!("Request for {attribute:?} successful!\n{output:#?}");
            }
        } else {
            // Match call from user/webclient
            log::debug!("[PROFILE] Received request from external address!");
        }
    }
}

// Test user UUID: 1816fb50-e925-4550-a1ef-573caf45ef66
#[derive(serde::Serialize, serde::Deserialize, Debug)]
struct Profile {
    user: String,
    dietary_preferences: HashMap<String, String>,
    dietary_restrictions: HashMap<String, String>,
    available_tools: HashMap<String, String>,
    available_ingredients: HashMap<String, String>,
}

#[derive(PartialEq, Eq, Hash, Debug)]
enum ProfileAttribute {
    Preferences,
    Restrictions,
    Tools,
    Ingredients,
    Uuid,
    Unknown,
}

async fn read_profile_attributes(
    user_id: &str,
    attribute: &[ProfileAttribute],
    client: &SupabaseClient,
) -> Result<HashMap<ProfileAttribute, HashMap<String, String>>, String> {
    use serde_json::Value;
    use supabase_rs::query::QueryBuilder;

    let columns: Vec<&str> = attribute
        .iter()
        .map(|attr| match attr {
            ProfileAttribute::Preferences => "dietary_preferences",
            ProfileAttribute::Restrictions => "dietary_restrictions",
            ProfileAttribute::Tools => "available_tools",
            ProfileAttribute::Ingredients => "available_ingredients",
            ProfileAttribute::Uuid => "user",
            ProfileAttribute::Unknown => "*",
        })
        .collect();

    let profile_query: QueryBuilder = client
        .select("Profile")
        .eq("user", user_id)
        .columns(columns.clone());

    let output: Vec<Value> = profile_query.execute().await?;

    if output.is_empty() {
        Err("Query returned empty!".to_string())
    } else if output.len() > 1 {
        Err("Query returned multiple profiles. Please check input parameters".to_string())
    } else {
        let row = output.first().unwrap();
        let mapped_values: HashMap<ProfileAttribute, HashMap<String, String>> =
            HashMap::from_iter(columns.iter().map(|&entry| {
                let key: ProfileAttribute = match entry {
                    "dietary_preferences" => ProfileAttribute::Preferences,
                    "dietary_restrictions" => ProfileAttribute::Restrictions,
                    "available_tools" => ProfileAttribute::Tools,
                    "available_ingredients" => ProfileAttribute::Ingredients,
                    _ => ProfileAttribute::Unknown,
                };

                log::debug!("row: {row:#?}");

                let value: HashMap<String, String> = if key == ProfileAttribute::Unknown {
                    HashMap::new()
                } else {
                    let entry_value: Value = row.get(entry).unwrap_or(&Value::Null).clone();

                    serde_json::from_value(entry_value).unwrap_or(HashMap::new())
                };

                (key, value)
            }));
        Ok(mapped_values)
    }
}

async fn fetch_profile(user_id: &str, client: &SupabaseClient) -> Result<Profile, String> {
    use serde_json::Value;
    use supabase_rs::query::QueryBuilder;

    let profile_query: QueryBuilder = client.select("Profile").eq("user", user_id).columns(vec![
        "dietary_preferences",
        "dietary_restrictions",
        "available_tools",
        "available_ingredients",
        "user",
    ]);
    let row: Vec<Value> = profile_query.execute().await?;

    if !row.is_empty() {
        let profile_object: String = row.first().unwrap().to_string();
        match serde_json::from_str::<Profile>(&profile_object) {
            Ok(profile) => {
                log::debug!("Successfully fetched profile: {profile:#?}");
                Ok(profile)
            }
            Err(e) => {
                log::debug!("Object: {profile_object}");
                log::warn!("Deserialisation Error: {e}");
                Err("[PROFILE] Failed to deserialise noon-empty DB result".to_string())
            }
        }
    } else {
        Err("[PROFILE] Failed to deserialise DB result".to_string())
    }
}
