use supabase_rs::SupabaseClient;

pub mod auth;
pub mod profile;

fn init_supabase_client() -> supabase_rs::errors::Result<SupabaseClient> {
    use supabase_rs::errors::ErrorTypes as SupabaseError;

    const SUPABASE_CREDS: &str = "../sb.uk";

    if let Ok(mut file) = std::fs::File::open(SUPABASE_CREDS) {
        use std::io::Read;

        let mut contents: String = String::new();
        let _ = file.read_to_string(&mut contents);
        if contents.is_empty() {
            log::warn!("[ROUTER] Supabase API creds missing!");
            Err(SupabaseError::ApiKeyMissing)
        } else {
            let mut lines: std::str::Lines = contents.lines();
            let supabase_url: String = lines.next().unwrap_or("").to_string();
            let supabase_key: String = lines.next().unwrap_or("").to_string();

            if supabase_key.is_empty() || supabase_url.is_empty() {
                log::warn!("[ROUTER] Failed to read API creds correctly!");
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
