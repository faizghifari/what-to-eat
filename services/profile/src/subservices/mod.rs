use supabase_rs::SupabaseClient;

pub mod auth;
pub mod profile;

fn init_supabase_client() -> Result<SupabaseClient, supabase_rs::errors::ErrorTypes> {
    let supabase_url: String = env!("SUPABASE_URL").to_string();
    let supabase_key: String = env!("SUPABASE_KEY").to_string();
    SupabaseClient::new(supabase_url, supabase_key)
}
