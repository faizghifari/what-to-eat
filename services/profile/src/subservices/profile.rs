use supabase_rs::SupabaseClient;

use super::init_supabase_client;

// Profile service
pub async fn run() -> std::io::Result<()> {
    // Authenticate service with Supabase / launch client
    let client: Result<SupabaseClient, _> = init_supabase_client();
    if let Err(e) = client {
        log::error!("[PROFILE] Failed to create Supabase client: {e}");
        return Err(std::io::Error::new(
            std::io::ErrorKind::PermissionDenied,
            "Failed to authenticate Supabase client: {e}",
        ));
    }
    let _client: SupabaseClient = client.unwrap();
    log::debug!("[PROFILE] Created SupabaseClient successfully!");

    Ok(())
}
